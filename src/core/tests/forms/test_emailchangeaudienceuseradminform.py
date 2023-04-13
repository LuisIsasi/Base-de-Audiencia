import logging
from unittest import mock

from django import test
from django.forms import ValidationError
from django.forms.models import modelform_factory
from model_mommy import mommy
from sailthru_sync import models as sync_models
from sailthru_sync.errors import SailthruErrors

from ... import admin as core_admin, models as core_models
from .mock_sailthru import MockedSailthruClient


@test.override_settings(SAILTHRU_SYNC_SIGNALS_ENABLED=False, RAVEN_CONFIG={'dsn': None})
class EmailChangeFormTest(test.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self):
        super().setUp()
        self.EmailChangeForm = modelform_factory(
            core_models.EmailChangeAudienceUser,
            form=core_admin.EmailChangeAudienceUserAdminForm,
            fields="__all__"
        )

    def test_clean_email(self):

        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')

        form = self.EmailChangeForm(instance=user)
        form.cleaned_data = {}

        form.cleaned_data['email'] = " b@a.com "
        form.clean_email()

        form.cleaned_data['email'] = None
        with self.assertRaises(ValidationError):
            form.clean_email()

        form.cleaned_data['email'] = '  '
        with self.assertRaises(ValidationError):
            form.clean_email()

        form.cleaned_data['email'] = ''
        with self.assertRaises(ValidationError):
            form.clean_email()

        form.cleaned_data['email'] = user.email
        with self.assertRaises(ValidationError):
            form.clean_email()

        form.cleaned_data['email'] = user.email + "\t"
        with self.assertRaises(ValidationError):
            form.clean_email()

    def test_obtain_sync_lock(self):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._obtain_sync_lock()
        self.assertEqual(sync_models.SyncLock.objects.filter(pk=form._sync_lock.pk).count(), 1)

    def test_obtain_sync_lock_user_deleted(self):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        user.delete()
        with self.assertRaises(ValidationError):
            form._obtain_sync_lock()

    def test_delete_sync_lock(self):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form._obtain_sync_lock()
        form._delete_sync_lock()
        with self.assertRaises(sync_models.SyncLock.DoesNotExist):
            sync_models.SyncLock.objects.get(pk=form._sync_lock.pk)

    @test.override_settings(SAILTHRU_SYNC_ENABLED=False)
    @mock.patch('core.admin.sailthru_client')
    def test_setting_override(self, get_sailthru_client):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form.cleaned_data = {}
        form.clean()
        self.assertFalse(get_sailthru_client.called)

    @mock.patch('core.admin.sailthru_client')
    def test_sync_to_sailthru(self, get_sailthru_client):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form._sync_to_sailthru({})
        self.assertTrue(get_sailthru_client.called)

    @mock.patch('core.admin.sailthru_client')
    def test_sync_to_sailthru_on_error(self, get_sailthru_client):
        client = MockedSailthruClient()
        client.api_post_raise_exception = True
        get_sailthru_client.return_value = client

        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._sync_to_sailthru({})

    def test_get_sync_data(self):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        new_user = mommy.make('core.EmailChangeAudienceUser', email='b@a.com')
        form = self.EmailChangeForm(instance=user)
        data = form._get_sync_data(user, new_user)
        self.assertEqual({'id', 'key', 'keys', 'fields'}, set(data.keys()))
        self.assertEqual(data['id'], user.email)
        self.assertEqual(data['key'], 'email')
        self.assertEqual(data['keys']['email'], new_user.email)
        self.assertEqual(data['fields']['keys'], 1)

        new_user.email = None
        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._get_sync_data(user, new_user)

        user.email = None
        new_user.email = 'b@a.com'
        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._get_sync_data(user, new_user)

    def test_check_response_ok(self):
        response = MockedSailthruClient.MockedResponse()
        response.ok = False

        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._check_response_ok(response)

        response.ok = True
        response.body = {}
        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._check_response_ok(response)

    def test_re_request_necessary(self):
        response = MockedSailthruClient.MockedResponse()
        response.ok = True

        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form._obtain_sync_lock()
        self.assertFalse(form._re_request_necessary(response))

        response.ok = False
        response.response_error_code = SailthruErrors.OTHER_ERROR
        self.assertFalse(form._re_request_necessary(response))

        response.response_error_code = SailthruErrors.INVALID_EMAIL
        response.response_error_message = "Invalid email: b@b.com"
        self.assertFalse(form._re_request_necessary(response))

        response.response_error_message = "Invalid email: a@a.com"
        self.assertTrue(form._re_request_necessary(response))

    def test_get_new_user_sync_data(self):
        old_email = "a@a.com"
        user = mommy.make('core.EmailChangeAudienceUser', email=old_email)
        form = self.EmailChangeForm(instance=user)
        new_email = "b@b.com"
        data = form._get_new_user_sync_data(user, new_email)
        self.assertEqual(data["id"], new_email)
        self.assertEqual(old_email, user.email)

        form._obtain_sync_lock()
        with self.assertRaises(ValidationError):
            form._get_new_user_sync_data(user, None)

    def test_verify_sid(self):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com', sailthru_id='adf')
        form = self.EmailChangeForm(instance=user)
        form._obtain_sync_lock()

        response = MockedSailthruClient.MockedResponse()
        response.body = {
            'keys': {
                'sid': user.sailthru_id
            }
        }

        form._verify_sid(response, user.sailthru_id)

        response.body['keys']['sid'] = user.sailthru_id + 'adsf'
        with self.assertRaises(ValidationError):
            form._verify_sid(response, user.sailthru_id)

    @test.override_settings(SAILTHRU_SYNC_ENABLED=False)
    def test_clean_sync_disabled(self):
        EmailForm = type(
            'Foo',
            (core_admin.EmailChangeAudienceUserAdminForm,),
            {
                '_obtain_sync_lock': mock.MagicMock(),
            }
        )

        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        Form = modelform_factory(core_models.EmailChangeAudienceUser, form=EmailForm, fields="__all__")
        form = Form(instance=user)
        form.cleaned_data = {
            'email': 'a@a.com',
        }
        form.clean()
        self.assertFalse(form._obtain_sync_lock.called)

    @test.override_settings(SAILTHRU_SYNC_ENABLED=True)
    def test_clean(self):
        """Previous bits have been tested, so this will just ensure that they are called.
        """
        EmailForm = type(
            'Foo',
            (core_admin.EmailChangeAudienceUserAdminForm,),
            {
                '_obtain_sync_lock': mock.MagicMock(),
                '_get_sync_data': mock.MagicMock(),
                '_sync_to_sailthru': mock.MagicMock(),
                '_re_request_necessary': mock.MagicMock(),
                '_get_new_user_sync_data': mock.MagicMock(),
                '_check_response_ok': mock.MagicMock(),
                '_verify_sid': mock.MagicMock(),
                '_delete_sync_lock': mock.MagicMock(),
            }
        )

        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        Form = modelform_factory(core_models.EmailChangeAudienceUser, form=EmailForm, fields="__all__")
        form = Form(instance=user)
        form.cleaned_data = {
            'email': 'a@a.com',
        }
        form.clean()

        self.assertTrue(form._obtain_sync_lock.called)
        self.assertTrue(form._get_sync_data.called)
        self.assertTrue(form._sync_to_sailthru.called)
        self.assertTrue(form._re_request_necessary.called)
        self.assertTrue(form._get_new_user_sync_data.called)
        self.assertTrue(form._check_response_ok.called)
        self.assertTrue(form._verify_sid.called)
        self.assertTrue(form._delete_sync_lock.called)

    @test.override_settings(SAILTHRU_SYNC_ENABLED=False)
    @mock.patch('core.admin.sync_user_basic.apply_async')
    def test_save_sync_disabled(self, async):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form.cleaned_data = {
            'email': 'a@a.com',
        }
        form.save()
        self.assertFalse(async.called)

    @test.override_settings(SAILTHRU_SYNC_ENABLED=True)
    @mock.patch('core.admin.sync_user_basic.apply_async')
    def test_save_sync(self, async):
        user = mommy.make('core.EmailChangeAudienceUser', email='a@a.com')
        form = self.EmailChangeForm(instance=user)
        form.cleaned_data = {
            'email': 'a@a.com',
        }
        form._aud_user = user
        form.save()
        self.assertTrue(async.called_with([user.pk]))
