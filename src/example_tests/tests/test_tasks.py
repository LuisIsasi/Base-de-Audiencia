from django import test

from ..tasks import return_noodles

@test.override_settings(CELERY_ALWAYS_EAGER=True)
class TestTaskTestCase(test.TestCase):
    """
    The always eager setting is used so we can fetch the response.
    """
    def test_noodles(self):
        result = return_noodles.delay()
        self.assertEqual(result.get(), "noodles")
        self.assertTrue(result.successful())
