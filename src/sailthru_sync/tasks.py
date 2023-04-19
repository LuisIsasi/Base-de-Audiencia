import random
from datetime import timedelta

from audb import celery_app
from celery.utils.log import get_task_logger
from core.decorators import throttle
from core.models import AudienceUser
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
import sentry_sdk

from . import models as m, utils
from .converter.audienceuser_to_sailthru import AudienceUserToSailthru
from .decorators import log_on_error
from .errors import SailthruErrors


logger = get_task_logger(__name__)


@celery_app.task(bind=True)
@log_on_error("Sailthru sync basic: unhandled exception.")
@throttle(
    interval_seconds=settings.SAILTHRU_TASK_THROTTLE_INTERVAL, logger_name=__name__
)
def sync_user_basic(self, user_pk):
    logger.info("Starting sailthru sync for user %s.", str(user_pk))
    try:
        aud_user = AudienceUser.objects.get(pk=user_pk)
    except AudienceUser.DoesNotExist as e:
        msg = "Sailthru sync basic: Unable to find user."
        sentry_sdk.capture_exception(e)
        logger.error("Sailthru sync basic: Unable to find user: %s", str(user_pk))
        return
    try:
        lock = m.SyncLock.objects.get_from_locked_instance(aud_user)
    except m.SyncLock.DoesNotExist:
        pass
    else:
        max_age = timedelta(minutes=1)
        if lock.age > max_age:
            msg = "Sailthru sync basic: User locked from syncing with Sailthru."
            with sentry_sdk.push_scope() as scope:
                scope.set_extra("user", {"pk": aud_user.pk})
                scope.set_extra(
                    "lock",
                    {
                        "pk": lock.pk,
                        "Age (minutes)": lock.age.total_seconds() / 60,
                        "Max age (minutes)": max_age.total_seconds() / 60,
                    },
                )
                sentry_sdk.capture_message(msg)
            logger.warn(
                "Sailthru sync basic: Sync lock %s for user %s is old.",
                str(lock.pk),
                str(user_pk),
            )
        else:
            logger.warn(
                "Sailthru sync basic: Sync lock exists for user %s.", str(user_pk)
            )
            self.retry(
                countdown=settings.SAILTHRU_TASK_THROTTLE_INTERVAL + 1
            )  # This should hopefully ensure we run a sync event without hitting a stale update lock

    try:
        converter = AudienceUserToSailthru(aud_user)
        request_data = converter.convert()
    except Exception as e:
        msg = "Sailthru sync basic: Unable to convert user {}: {}.".format(user_pk, e)
        m.SyncFailure.objects.from_message(msg, aud_user)
        sentry_sdk.capture_exception(e)
        logger.error(msg)
        return

    try:
        response = utils.sailthru_client().api_post("user", request_data)
    except Exception as e:
        msg = "Sailthru sync basic: Problem occured during request to Sailthru."
        sentry_sdk.capture_exception(e)
        logger.error(
            "Sailthru sync basic: Problem occured during request to Sailthru: %s",
            str(e),
        )
        throttle_interval = settings.SAILTHRU_TASK_THROTTLE_INTERVAL
        max_retries = 10
        countdown = throttle_interval + (2**self.request.retries)  # Max = 17 min
        with_jitter = random.randint(throttle_interval, countdown)
        self.retry(exc=e, countdown=with_jitter, max_retries=max_retries)
        return

    if not response.is_ok():
        msg = "Sailthru sync basic: Sailthru rejected request to sync."
        m.SyncFailure.objects.from_sailthru_error_response(msg, aud_user, response)
        logger.error(
            "Sailthru sync basic: Sailthru rejected request to sync for user %s (%s)",
            str(aud_user.pk),
            aud_user.email,
        )
        return

    try:
        data = response.get_body()
        sid = data["keys"]["sid"]
    except KeyError:
        msg = "Sailthru sync basic: Sailthru response missing expected values."
        m.SyncFailure.objects.from_sailthru_response(msg, aud_user, response)
        logger.error(
            "Sailthru sync basic: Sailthru response missing expected values on user %s (%s).",
            str(aud_user.pk),
            aud_user.email,
        )
    else:
        changed_sid = False
        with transaction.atomic():
            aud_user.refresh_from_db()
            if aud_user.sailthru_id:
                changed_sid = sid != aud_user.sailthru_id
            else:
                AudienceUser.objects.filter(pk=aud_user.pk).update(sailthru_id=sid)
            """
            TODO: this idea made resubs more complicated. I'm commenting it out for
            now. Maybe remove it later if we don't come across problems.
            """
            # utils.compare_and_update_optout(aud_user, sailthru_optout)
        if changed_sid:
            msg = (
                "Sailthru sync basic: Sailthru attempted to change the synced"
                " user's Sailthru ID from {} to {}."
            ).format(aud_user.sailthru_id, sid)
            m.SyncFailure.objects.from_sailthru_response(msg, aud_user, response)
            logger.error(msg)
            return
    logger.info(
        "Finished sailthru sync for user %s (%s).", str(aud_user.pk), aud_user.email
    )


@celery_app.task(bind=True)
@log_on_error("Send sync failure notifications: unhandled exception.")
def send_sync_failure_notifications(self):
    logger.info(
        "Send sync failure notifications: Checking if there are any groups to notify..."
    )
    groups = m.SyncFailureNotificationGroup.objects.prefetch_related(
        "interested_group", "interested_group__user_set"
    ).all()

    if not groups:
        logger.info(
            "Send sync failure notifications: There are no groups interested in notifications."
        )
        logger.info("Send sync failure notifications: Complete.")
        return

    logger.info(
        "Send sync failure notifications: Checking if there are any failures of interest..."
    )
    interested_errors = {error for group in groups for error in group.interested_errors}
    failures = m.SyncFailure.objects.filter(
        acknowledged=False, resolved=False, sailthru_error_code__in=interested_errors
    )

    if not failures:
        logger.info(
            "Send sync failure notifications: There are no failures of interest."
        )
        logger.info("Send sync failure notifications: Complete.")
        return

    for group in groups:
        interested_failures = [
            failure
            for failure in failures
            if failure.sailthru_error_code in group.interested_errors
        ]
        if not interested_failures:
            continue
        subject = "[Audb][Sync failures][{}] Notification".format(
            group.interested_group.name
        )
        message = construct_message_from_failures(interested_failures)
        emails = set()
        for user in group.interested_group.user_set.all():
            if user.email:
                emails.add(user.email)
        logger.info(
            "Send sync failure notifications: Sending email to group '{}'...".format(
                group.interested_group.name
            )
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(emails),
            fail_silently=False,
        )

    logger.info("Send sync failure notifications: Acknowledging failures...")
    failures.update(acknowledged=True)
    logger.info("Send sync failure notifications: Complete.")


def construct_message_from_failures(failures):
    hr_errors = dict(
        (str(error_code), msg["short-msg"])
        for error_code, msg in SailthruErrors.MESSAGES.items()
    )

    counts = {}
    for failure in failures:
        if failure.sailthru_error_code not in counts:
            counts[failure.sailthru_error_code] = 0
        counts[failure.sailthru_error_code] += 1

    sorted_failures = sorted(
        [(hr_errors[failure.sailthru_error_code], failure) for failure in failures],
        key=lambda x: x[0],
    )

    message = [
        "Uh oh!",
        "",
        "New sync failures have occured since the last notification and require your attention.",
        "",
    ]
    current_msg = ""
    for short_msg, failure in sorted_failures:
        if short_msg != current_msg:
            if current_msg != "":
                message.append("")
            current_msg = short_msg
            template = "There were {counts} failure(s) based on the sailthru response '{response}'."
            context = {
                "counts": counts[failure.sailthru_error_code],
                "response": short_msg,
            }
            message.append(template.format(**context))
        message.append(failure.get_admin_url(full_url=True))

    message.append("\n\nHave a nice day!")

    return "\n".join(message)
