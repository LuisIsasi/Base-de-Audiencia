from django.conf import settings
from django.utils import timezone
from sailthru.sailthru_client import SailthruClient


def sailthru_client(request_timeout=10):
    sc = SailthruClient(settings.SAILTHRU_API_KEY, settings.SAILTHRU_API_SECRET)
    return sc


def compare_and_update_optout(user, email_optout):
    """
    Compares `email_optout` from Sailthru API response to current
    `user.sailthru_optout`.  If the two differ, it updates the user's optout
    optout status.

    Note: intended to be used after reading from sailthru (post save).  By default
    sync to sailthru will be disabled.
    """
    if email_optout != user.sailthru_optout:
        user.disable_sync()

        if user.sailthru_optout is None:
            effective_date = user.created
            comment = "Initial optout status (from sailthru API response)"
        else:
            effective_date = timezone.now()
            comment = "Updating to match sailthru (from sailthru API response)"

        user.record_optout(email_optout, comment, effective_date=effective_date)
