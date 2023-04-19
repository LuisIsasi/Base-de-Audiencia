import csv
from datetime import datetime
from pytz import exceptions

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import AudienceUser


COLUMN_EMAIL = "Email"
COLUMN_OPTOUT = "Optout"
COLUMN_OPTOUT_TIME = "Optout Time"


def parse_datetime(str_value):
    # print("Attempting to parse {}".format(str_value))
    dt_value = datetime.strptime(str_value, "%Y/%m/%d %H:%M:%S")
    try:
        return timezone.make_aware(dt_value)
    except exceptions.AmbiguousTimeError:
        dt_value = dt_value.replace(hour=0, minute=0, second=0)
        return timezone.make_aware(dt_value)


class Command(BaseCommand):
    help = """
        Given a CSV export from Sailthru with `{}` and `{}`
        column headers, updates every matching AudienceUser with the appropriate
        optout status.
        """.format(
        COLUMN_EMAIL, COLUMN_OPTOUT
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            nargs=1,
            help=".csv file with `{}` and `{}` columns".format(
                COLUMN_EMAIL, COLUMN_OPTOUT
            ),
        )
        parser.add_argument(
            "--limit",
            nargs=1,
            help="Max number of rows to process",
            default=["999999999"],
        )

    def handle(self, *args, **options):
        if not options["file"]:
            raise CommandError("--file must be specified")

        with open(options["file"][0], "r") as csvfile:
            reader = csv.reader(csvfile)

            header_row = next(reader, None)

            optout_index = header_row.index(COLUMN_OPTOUT)
            optout_time_index = header_row.index(COLUMN_OPTOUT_TIME)
            email_index = header_row.index(COLUMN_EMAIL)

            found = 0
            not_found = 0
            rows_completed = 0
            rows_max = int(options["limit"][0])

            for row in reader:
                email = row[email_index]
                optout = row[optout_index]
                try:
                    optout_time = parse_datetime(row[optout_time_index])
                    comment = "Imported from Sailthru to audb (via CSV export)"
                except ValueError:
                    optout_time = timezone.now()
                    comment = (
                        "Imported from Sailthru to audb (via CSV export). "
                        "No date included. Effective Date set to now."
                    )
                try:
                    user = AudienceUser.objects.get(email=email)
                    """
                    Can't easily disable sync because triggered unsubs will trigger
                    sync.  This is ok for now because we'll want those updates to occur
                    anyway.
                    """
                    # user.disable_sync()

                    user.record_optout(optout, comment, effective_date=optout_time)
                    found += 1
                except AudienceUser.DoesNotExist:
                    not_found += 1

                rows_completed += 1

                if rows_completed % 1000 == 0:
                    print(
                        (
                            "Completed {} rows so far "
                            "({} emails found; {} not found)"
                        ).format(rows_completed, found, not_found)
                    )

                if rows_completed >= rows_max:
                    break

            print(
                (
                    "--------------\n--------------\n"
                    "Import completed.\n"
                    "{} total rows; {} emails found; {} not found\n"
                    "--------------\n--------------"
                ).format(rows_completed, found, not_found)
            )
