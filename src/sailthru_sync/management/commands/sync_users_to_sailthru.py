from argparse import RawTextHelpFormatter

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from core.models import AudienceUser
from ...tasks import sync_user_basic


class Command(BaseCommand):
    help = """
    Sync a particular user to Sailthru:
        manage.py sync_users_to_sailthru --user <AudienceUser pk>
    or
        manage.py sync_users_to_sailthru --user <AudienceUser email>

    Sync all users in the db to Sailthru:
        manage.py sync_users_to_sailthru --range all

    Sync the first 500 users returned from the db when ordered by ascending pk:
        manage.py sync_users_to_sailthru --range 0:500
    """

    def add_arguments(self, parser):
        # monkey-patch so that we do not lose the line-breaks in the help text
        parser.formatter_class = RawTextHelpFormatter

        parser.add_argument('--user', nargs=1, type=str)
        parser.add_argument('--range', nargs=1, type=str)

    def _validate_options(self, options):
        if not options['user'] and not options['range']:
            raise CommandError("Must supply either '--user' or '--range' arguments.")

        if options['user'] and options['range']:
            raise CommandError("Supply only one of the following arguments: '--user', '--range'.")

        if options['range'] and options['range'][0] != 'all':
            invalid_range = False
            if len(options['range'][0].split(':')) != 2:
                invalid_range = True
            if not all([x.isdigit() for x in options['range'][0].split(':')]):
                invalid_range = True
            if invalid_range:
                raise CommandError('--range must specify either "all" or a slice like "0:500".')

    def handle(self, *args, **options):
        self._validate_options(options)

        if not settings.SAILTHRU_SYNC_ENABLED:
            raise ImproperlyConfigured(
                "Sailthru sync management command cannot run because Sailthru sync is "
                "currently disabled."
            )

        if options['user']:
            user_arg = options['user'][0]

            try:
                if user_arg.isdigit():
                    user = AudienceUser.objects.get(pk=int(user_arg))
                else:
                    user = AudienceUser.objects.get(email=user_arg)
            except AudienceUser.DoesNotExist:
                raise CommandError('Could not find user.')

            if not user.email:
                raise CommandError('Cannot sync users that do not have email addresses.')

            self.stdout.write("Queuing Sailthru sync for user: {}".format(user_arg))
            sync_user_basic.apply_async([user.pk])

        elif options['range']:
            qs = AudienceUser.objects.all().order_by('id')
            if options['range'][0] != 'all':
                start, end = [int(x) for x in options['range'][0].split(':')]
                qs = qs[start:end]
            qs_count = qs.count()
            self.stdout.write(
                'Queuing Sailthru sync for {} user{} (users without email addresses will '
                'be skipped) . . .'
                .format(qs_count, 's' if qs_count != 1 else '')
            )
            for user in qs:
                if user.email:
                    sync_user_basic.apply_async([user.pk])
            self.stdout.write('. . . done queuing.')

        else:
            raise CommandError("No recognized arguments found.")
