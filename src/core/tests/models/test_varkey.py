from django.test import TestCase
from model_mommy import mommy


class VarKeyTestCase(TestCase):
    def test_str(self):
        key = mommy.make("core.VarKey", key="a", type="other", sync_with_sailthru=True)
        self.assertIn(key.key, str(key))
        self.assertIn(key.type, str(key))
        self.assertIn("synced", str(key))

        key.sync_with_sailthru = False
        self.assertIn("not synced", str(key))

        key.key = ""
        self.assertEqual("", str(key))

        key.key = "a"
        key.type = ""
        self.assertEqual("", str(key))
