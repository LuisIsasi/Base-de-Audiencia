from django import test
from django.forms import ValidationError
from django.forms.models import modelform_factory
from model_mommy import mommy

from ... import admin as core_admin, models as core_models


@test.override_settings(SAILTHRU_SYNC_SIGNALS_ENABLED=False, RAVEN_CONFIG={'dsn': None})
class AudienceUserFormTest(test.TestCase):

    def test_clean_vars(self):
        user = mommy.make('core.AudienceUser', email='a@a.com')

        Form = modelform_factory(core_models.AudienceUser, form=core_admin.AudienceUserForm, fields="__all__")
        form = Form(instance=user)
        form.cleaned_data = {
            'vars': {
                'a': 'b',
                'b': 'b',
            }
        }
        form.clean_vars()

        form.cleaned_data['vars']['a_DUPLICATE_VAR_1'] = 'a'
        with self.assertRaises(ValidationError):
            form.clean_vars()
        del form.cleaned_data['vars']['a_DUPLICATE_VAR_1']

        form.cleaned_data['vars']['a b'] = 'a'
        with self.assertRaises(ValidationError):
            form.clean_vars()
        del form.cleaned_data['vars']['a b']

        form.cleaned_data['vars']['asset_test'] = 'a'
        with self.assertRaises(ValidationError):
            form.clean_vars()

        form.cleaned_data['vars']['a_DUPLICATE_VAR_1'] = 'a'
        form.cleaned_data['vars']['a b'] = 'a'
        with self.assertRaises(ValidationError):
            form.clean_vars()
