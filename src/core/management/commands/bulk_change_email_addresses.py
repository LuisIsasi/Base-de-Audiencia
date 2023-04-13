from argparse import RawTextHelpFormatter

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from core.models import AudienceUser
from sailthru_sync.models import SyncLock
from sailthru_sync.utils import sailthru_client


class Command(BaseCommand):
    help = """
    Use this command to change users' email addresses __ONLY WHEN__ a user
    with the new email address does not exist, _ie_ when no merging
    of user profiles needs to be considered.

    Specify the input file with ``--file``. This file should contain old/new
    email address pairs like:

        old@email.com,new@email.com
    """

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        parser.add_argument('--file', nargs=1, type=str)

    def handle(self, *args, **options):
        if not settings.SAILTHRU_SYNC_ENABLED:
            raise ImproperlyConfigured(
                "Cannot run because Sailthru sync is currently disabled."
            )

        if not options['file']:
            raise CommandError('--file must be specified')

        with open(options['file'][0], 'r') as input_file:
            pairs = [x.strip().split(',') for x in input_file.readlines()]
            self._sanity_check_pairs(pairs)
            for old_email, new_email in pairs:
                self._change_email(old_email, new_email)

    @staticmethod
    def _sanity_check_pairs(pairs):
        if not pairs:
            raise CommandError('No old/new email pairs found')
        if [x for x in pairs if len(x) != 2]:
            raise CommandError('Input file should contain one comma-separated pair on each line')

        old_emails = [x[0] for x in pairs]
        new_emails = [x[1] for x in pairs]

        for old_email, new_email in pairs:
            if not old_email or not new_email:
                raise CommandError('Cannot have empty emails')
            if old_emails.count(old_email) > 1:
                raise CommandError('Same old email found in multiple pairs: {}'.format(old_email))
            if new_emails.count(new_emails) > 1:
                raise CommandError('Same new email found in multiple pairs: {}'.format(new_email))
            if old_email in new_emails:
                raise CommandError(
                    'Old email being used as a new email in one or more pairs: {}'.format(old_email)
                )
            if new_email in old_emails:
                raise CommandError(
                    'New email being used as a old email in one or more pairs: {}'.format(new_email)
                )
            try:
                AudienceUser.objects.get(email=old_email)
            except AudienceUser.DoesNotExist:
                raise CommandError('User with email does not exist in audb: {}'.format(old_email))
            if AudienceUser.objects.filter(email=new_email).exists():
                raise CommandError('Update-to email already exists: {}'.format(new_email))

    def _check_st_response(self, user, new_email, response_body):
        st_sync_email = response_body.get('keys', {}).get('email', None)
        st_sync_sid = response_body.get('keys', {}).get('sid', None)
        if st_sync_email != new_email:
            raise Exception('expected email not gotten, instead: {}'.format(st_sync_email))
        if st_sync_sid != user.sailthru_id:
            raise Exception('SIDs do not match: {} {}'.format(st_sync_sid, user.sailthru_id))

    def _change_email(self, old_email, new_email):
        self.stdout.write('changing: {} > {}'.format(old_email, new_email))

        user = AudienceUser.objects.get(email=old_email)

        try:
            sync_lock = self._get_sync_lock(user)
        except Exception as e:
            self.stdout.write('[ERROR] {}'.format(e))
            return

        try:
            st_update = self._update_email_at_sailthru(old_email, new_email)
        except Exception as e:
            st_update = None
            self.stdout.write('[ERROR] {}'.format(e))
        finally:
            self._free_sync_lock(sync_lock)

        if not st_update:
            return

        response_body = st_update.get_body()
        try:
            self._check_st_response(user, new_email, response_body)
        except Exception as e:
            self.stdout.write('[ERROR] {}'.format(e))
            return

        user.email = new_email
        user.validate_and_save()

    def _update_email_at_sailthru(self, old_email, new_email):
        payload = {
            'id': old_email,
            'key': 'email',
            'keys': {
                'email': new_email,
            },
            'fields': {
                'keys': 1,
            },
        }
        response = sailthru_client().api_post("user", payload)
        if not response.is_ok():
            raise Exception(response.get_body())
        return response

    @staticmethod
    def _get_sync_lock(user):
        try:
            lock = SyncLock(locked_instance=user)
            with transaction.atomic():
                lock.save()
        except IntegrityError:
            raise Exception("This user is currently locked, preventing syncing with Sailthru.")
        return lock

    @staticmethod
    def _free_sync_lock(lock):
        lock.delete()
