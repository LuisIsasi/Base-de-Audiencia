import csv

from django.core.management.base import BaseCommand, CommandError

from sailthru_sync.utils import sailthru_client
from sailthru.sailthru_error import SailthruClientError


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--file", nargs=1, help=".csv file with list names in first column"
        )
        parser.add_argument("--job", nargs=1, help="Existing sailthru job_id")

    def list_erase(self, data):
        """
        data must be an array of strings (sailthru list names)
        """
        try:
            response = sailthru_client(request_timeout=120).api_post(
                "job",
                {
                    "job": "list_erase",
                    "report_email": "developer@govexec.com",
                    "lists": data,
                },
            )

            if response.is_ok():
                body = response.get_body()
                print(body)
            else:
                error = response.get_error()
                print("Error: " + error.get_message())
                print("Status Code: " + str(response.get_status_code()))
                print("Error Code: " + str(error.get_error_code()))

        except SailthruClientError as e:
            # Handle exceptions
            print("Exception")
            print(e)

    def job_status(self, job_id):
        """
        job_id is returned in list_erase call
        """
        try:
            response = sailthru_client().api_get("job", {"job_id": job_id})

            if response.is_ok():
                body = response.get_body()
                print(body)
            else:
                error = response.get_error()
                print("Error: " + error.get_message())
                print("Status Code: " + str(response.get_status_code()))
                print("Error Code: " + str(error.get_error_code()))

        except SailthruClientError as e:
            # Handle exceptions
            print("Exception")
            print(e)

    def handle(self, *args, **options):
        if options["job"]:
            return self.job_status(options["job"][0])

        if not options["file"]:
            raise CommandError("--file or --job must be specified")

        data = []

        with open(options["file"][0], "r", encoding="ISO-8859-1") as csvfile:
            reader = csv.reader(csvfile)
            # skip header
            next(reader, None)

            for row in reader:
                data.append(row[0].strip())

        # sailthru caps bulk list deletion at 1,000
        if len(data) > 1000:
            raise CommandError("Maximum of 1,000 lists at a time.")

        self.list_erase(data)
