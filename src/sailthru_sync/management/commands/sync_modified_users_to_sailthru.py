from argparse import RawTextHelpFormatter
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from core.models import AudienceUser
from ...tasks import sync_user_basic


class Command(BaseCommand):
    help = """
    Sync all users modified within date range to Sailthru

    Options:
        --start "%Y-%m-%d %H:%M:%S"
        --end "%Y-%m-%d %H:%M:%S"
    """

    DATE_RANGE_PATTERN = "%Y-%m-%d %H:%M:%S"

    def add_arguments(self, parser):
        # monkey-patch so that we do not lose the line-breaks in the help text
        parser.formatter_class = RawTextHelpFormatter

        parser.add_argument("--start", type=str)
        parser.add_argument("--end", type=str)

    def _parse_options(self, options):
        start = options.get("start")
        end = options.get("end")

        if not start or not end:
            raise CommandError("Must supply either '--start' and '--end' arguments.")

        try:
            start_date = datetime.strptime(start, self.DATE_RANGE_PATTERN)
            end_date = datetime.strptime(end, self.DATE_RANGE_PATTERN)
        except Exception as e:
            raise CommandError("Error parsing arguments. {0}".format(e))

        return start_date, end_date

    def handle(self, *args, **options):
        start_date, end_date = self._parse_options(options)

        if not settings.SAILTHRU_SYNC_ENABLED:
            raise ImproperlyConfigured(
                "Sailthru sync management command cannot run because Sailthru sync is "
                "currently disabled."
            )

        qs = AudienceUser.objects.filter(modified__gt=start_date, modified__lt=end_date)
        qs_count = qs.count()
        self.stdout.write(
            "Queuing Sailthru sync for {} user{} (users without email addresses will "
            "be skipped) . . .".format(qs_count, "s" if qs_count != 1 else "")
        )
        for user in qs:
            if user.email:
                sync_user_basic.apply_async([user.pk])
        self.stdout.write(". . . done queuing.")
