import csv
from datetime import datetime
from pytz import exceptions

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import AudienceUser


COLUMN_EMAIL = 'Email'
COLUMN_ID = 'Profile Id'
COLUMN_PROFILE_CREATED = 'Profile Created Date'


def parse_datetime(str_value):
    # print("Attempting to parse {}".format(str_value))
    dt_value = datetime.strptime(str_value, "%Y/%m/%d %H:%M:%S")
    try:
        return timezone.make_aware(dt_value)
    except exceptions.AmbiguousTimeError:
        dt_value = dt_value.replace(hour=0, minute=0, second=0)
        return timezone.make_aware(dt_value)


class Command(BaseCommand):
    help = (
        """
        Given a CSV export from Sailthru with `{}` and `{}`
        column headers, updates every matching AudienceUser with the appropriate
        optout status.
        """.format(COLUMN_ID, COLUMN_PROFILE_CREATED)
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            nargs=1,
            help='.csv file with `{}` and `{}` columns'.format(
                COLUMN_ID,
                COLUMN_PROFILE_CREATED
            )
        )
        parser.add_argument(
            '--limit',
            nargs=1,
            help='Max number of rows to process',
            default=["999999999"]
        )

    def handle(self, *args, **options):
        if not options['file']:
            raise CommandError('--file must be specified')

        with open(options['file'][0], 'r') as csvfile:
            reader = csv.reader(csvfile)

            header_row = next(reader, None)

            profile_created_index = header_row.index(COLUMN_PROFILE_CREATED)
            email_index = header_row.index(COLUMN_EMAIL)

            found = 0
            not_found = 0
            rows_completed = 0
            rows_max = int(options['limit'][0])

            for row in reader:
                email = row[email_index]
                profile_created_date = parse_datetime(row[profile_created_index])
                try:
                    user = AudienceUser.objects.get(email=email)
                    user.disable_sync()

                    user.record_optout(
                        "none",
                        "Imported initial optin from Sailthru to audb (via CSV export)",
                        effective_date=profile_created_date
                    )
                    found += 1
                except AudienceUser.DoesNotExist:
                    not_found += 1

                rows_completed += 1

                if rows_completed % 1000 == 0:
                    print((
                        "Completed {} rows so far "
                        "({} emails found; {} not found)"
                    ).format(
                        rows_completed,
                        found,
                        not_found
                    ))

                if rows_completed >= rows_max:
                    break

            print((
                "--------------\n--------------\n"
                "Import completed.\n"
                "{} total rows; {} emails found; {} not found\n"
                "--------------\n--------------"
            ).format(
                rows_completed,
                found,
                not_found
            ))
