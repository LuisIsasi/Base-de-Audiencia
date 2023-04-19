from argparse import RawTextHelpFormatter

from celery.utils.log import get_task_logger
from django.db import router
from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from core.models import AudienceUser
from sailthru_sync import converter as sync_converter
from sailthru_sync.converter.errors import ConversionError
from sailthru_sync.utils import sailthru_client
import sentry_sdk


sync_logger = get_task_logger("sailthru_sync.tasks")


class Command(BaseCommand):
    help = """
    Use this command to mass delete users from Audb and Sailthru

    Specify the input file with ``--file``. This file should contain email addresses
    """

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        parser.add_argument("--file", nargs=1, type=str)

    def handle(self, *args, **options):
        if not settings.SAILTHRU_SYNC_ENABLED:
            raise ImproperlyConfigured(
                "Cannot run because Sailthru sync is currently disabled."
            )

        if not options["file"]:
            raise CommandError("--file must be specified")

        with open(options["file"][0], "r") as input_file:
            pairs = [x.strip().split(",") for x in input_file.readlines()]

            # skip over header in first line
            for row in pairs[1:]:
                email_address = row[0]

                try:
                    user = AudienceUser.objects.get(email=email_address)
                except AudienceUser.DoesNotExist:
                    print("User: {} does not exist in Audb".format(str(email_address)))
                    continue

                data = self._get_sync_data(user)
                response = self._sync_to_sailthru(data, user)
                if not response.is_ok():
                    print("Sailthru failed for: {}".format(str(email_address)))
                    print(response.get_error().message)
                    continue

                using = router.db_for_write(user._meta.model)
                collector = NestedObjects(using=using)
                collector.collect([user])
                collector.delete()

    def _get_sync_data(self, user):
        try:
            sync_logger.debug(
                "Delete user (%s): converting user data to sailthru format.", str(user)
            )

            converter = sync_converter.AudienceUserToSailthruDelete(user)
            return converter.convert()
        except ConversionError as e:
            msg = "Problem occured during data conversion for sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.error("Delete user (%s): " + msg, str(user))

    def _sync_to_sailthru(self, data, user):
        try:
            sync_logger.debug("Delete user (%s): Posting data to sailthru.", str(user))
            response = sailthru_client().api_post("user", data)
            return response
        except Exception as e:
            msg = "Problem occured during request to Sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.error("Delete user (%s): " + msg, str(user))
