from django.test import TestCase
from django.utils.text import slugify
from model_mommy import mommy


class TestQuestionnaireTestCase(TestCase):
    def test_str(self):
        q = mommy.make("example_tests.TestQuestionnaire")
        self.assertEqual(str(q), q.name)

    def test_slug_from_name_pattern(self):
        q = mommy.make("example_tests.TestQuestionnaire")
        q.set_slug_from_name()
        self.assertEqual(slugify(q.name), q.slug)

    def test_slug_from_name_pattern_failed_before(self):
        q = mommy.make("example_tests.TestQuestionnaire", name="")
        q.set_slug_from_name()
        self.assertEqual(slugify(q.name), q.slug)
