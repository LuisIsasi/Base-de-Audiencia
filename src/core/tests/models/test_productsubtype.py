from django.core.exceptions import ValidationError
from django.test import TestCase
from model_mommy import mommy


class ProductSubtypeTestCase(TestCase):
    def test_str(self):
        ps = mommy.make("core.ProductSubtype", name="foo")
        self.assertEqual(str(ps), "foo")

    def test_no_name(self):
        ps = mommy.make("core.ProductSubtype")
        ps.name = None
        with self.assertRaises(ValidationError) as cm:
            ps.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ["name"])
        self.assertEqual(
            cm.exception.message_dict["name"], ["This field cannot be null."]
        )

    def test_blank_name(self):
        ps = mommy.make("core.ProductSubtype")
        ps.name = ""
        with self.assertRaises(ValidationError) as cm:
            ps.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ["name"])
        self.assertEqual(
            cm.exception.message_dict["name"], ["This field cannot be blank."]
        )
