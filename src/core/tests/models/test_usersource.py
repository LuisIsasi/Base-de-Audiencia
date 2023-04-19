from django.test import TestCase
from model_mommy import mommy


class UserSourceTestCase(TestCase):
    def test_str_name(self):
        source = mommy.make("core.UserSource")
        self.assertEqual(str(source), source.name)

    def test_str_none(self):
        source = mommy.make("core.UserSource")

        source.name = None
        source_str = str(source)
        self.assertEqual(str(source), "")
