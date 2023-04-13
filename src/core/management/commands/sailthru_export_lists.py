import csv
from datetime import datetime

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError

from sailthru_sync.utils import sailthru_client
from sailthru.sailthru_error import SailthruClientError


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_file = "/tmp/sailthru_lists.csv"
        self.sailthru_lists = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            nargs="*",
            help="Destination address(es) for .csv export"
        )

    def get_lists(self):
        try:
            response = sailthru_client().api_get("list", {})

            if response.is_ok():
                body = response.get_body()
                self.sailthru_lists = body["lists"]

            else:
                error = response.get_error()
                print("Error: " + error.get_message())
                print("Status Code: " + str(response.get_status_code()))
                print("Error Code: " + str(error.get_error_code()))

        except SailthruClientError as e:
            # Handle exceptions
            print("Exception")
            print(e)

    def create_csv(self):
        with open(self.output_file, 'w') as csvfile:
            fieldnames = ['name', 'list_id', 'type', 'email_count', 'valid_count', 'create_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for row in self.sailthru_lists:
                # convert datetime column
                try:
                    row['create_time'] = datetime.strptime(row['create_time'], "%a, %d %b %Y %H:%M:%S %z")
                except:
                    pass

                writer.writerow(row)

    def email_csv(self, recipients):
        email = EmailMessage(
            "Sailthru Lists",
            "Sailthru Lists attached as .csv file.",
            "noreply@govexec.com",
            recipients
        )
        email.attach_file(self.output_file, "text/csv")
        email.send()

    def handle(self, *args, **options):
        # if not options["email"]:
        #     raise CommandError("--email required for destination")

        self.get_lists()
        self.create_csv()
        if options["email"]:
            self.email_csv(options["email"])
