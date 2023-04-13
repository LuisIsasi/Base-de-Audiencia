from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver

from .. import models as core_models


@receiver(post_save, sender=core_models.AudienceUser, dispatch_uid='core::signals::record_user_vars_history')
def record_user_vars_history(sender, **kwargs):
    user = kwargs.get('instance')
    if user:
        history = core_models.UserVarsHistory.objects.filter(audience_user=user).order_by("-timestamp")
        if not history:
            core_models.UserVarsHistory.objects.validate_and_create(
                audience_user=user, vars=user.vars
            )
        else:
            if user.vars != history[0].vars:
                core_models.UserVarsHistory.objects.validate_and_create(
                    audience_user=user, vars=user.vars
                )


@receiver(post_save, sender=core_models.AudienceUser, dispatch_uid='core::signals::update_var_keys')
def update_var_keys(sender, **kwargs):
    user = kwargs.get('instance')
    if user and user.vars:
        for key in [k.strip() for k in user.vars.keys()]:
            try:
                core_models.VarKey.objects.get(key=key)
            except core_models.VarKey.DoesNotExist:
                try:
                    core_models.VarKey.objects.validate_and_create(key=key, type='other')
                except (IntegrityError, ValidationError):  # pragma: no cover
                    # handle race conditions: was it created elsewhere just now?
                    if not core_models.VarKey.objects.filter(key=key).count():  # pragma: no cover
                        raise  # pragma: no cover


@receiver(post_save, sender=core_models.SubscriptionLog, dispatch_uid='core::signals::triggered_subscribes')
def triggered_subscribes(sender, **kwargs):
    sub_log = kwargs.get('instance')
    if not sub_log:
        return  # pragma: no cover

    if sub_log.action != 'subscribe':
        # only trigger related subscribes when it is a plain 'subscribe' action,
        # not _eg_ when the subscribe is done via the admin, or via a special data import
        # update, and definitely do not trigger subscribes when unsubscribing, obviously;
        # also do not recursively trigger subscribes, ie do not trigger them if the
        # subscribe action itself is a trigger
        return

    subscription = sub_log.subscription
    if not subscription:
        return  # pragma: no cover

    user = subscription.audience_user
    if not user:
        return  # pragma: no cover

    list_ = subscription.list
    if not list_:
        return  # pragma: no cover

    subscriptions = user.subscriptions.all()
    currently_subscribed_lists = [x.list.slug for x in subscriptions if x.active]
    currently_unsubscribed_lists = [x.list.slug for x in subscriptions if not x.active]

    for trigger in list_.subscription_triggers.all():
        related_list = trigger.related_list.slug
        if related_list in currently_subscribed_lists:
            continue

        ok_to_subscribe = (
            True
            if trigger.override_previous_unsubscribes else
            (related_list not in currently_unsubscribed_lists)
        )

        if ok_to_subscribe:
            comment = "subscribe triggered by {}".format(subscription.list.slug)
            if related_list in currently_unsubscribed_lists:
                comment += ' [overriding previous unsubscribe]'
            subscription.audience_user.list_subscribe(
                related_list, log_comment=comment, log_action='trigger'
            )
