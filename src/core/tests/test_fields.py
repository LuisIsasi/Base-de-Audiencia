from django.core.exceptions import ValidationError
from django.test import TestCase

from .. import fields as core_fields


class FieldsTestCase(TestCase):

    def test_vars_jsonfield_validator(self):
        with self.assertRaises(ValidationError):
            core_fields.vars_jsonfield_validator({"a space": "value"})

    def test_varkey_validator(self):
        with self.assertRaises(ValidationError):
            core_fields.varkey_validator("a space")
