from bs4 import BeautifulSoup
from django import test
from model_mommy import mommy


class TestQuestionnaireViewTestCase(test.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questionnaire = mommy.make("example_tests.TestQuestionnaire")

        c = test.Client()
        cls.rendered = c.get(cls.questionnaire.get_absolute_url())
        cls.soup = BeautifulSoup(cls.rendered.content, "html5lib")

    @classmethod
    def tearDownClass(cls):
        cls.questionnaire.delete()  # Not sure this is necessary

    def test_existence(self):
        q = mommy.make("example_tests.TestQuestionnaire")
        c = test.Client()

        url = q.get_absolute_url()
        response = c.get(url)
        self.assertEqual(response.status_code, 200)

        q.delete()
        response = c.get(url)
        self.assertEqual(response.status_code, 404)

    def test_content_name(self):
        ids = self.soup.find_all(id="questionnaire-name")
        self.assertEqual(len(ids), 1)
        name_id = ids[0].attrs["id"]
        self.assertFalse(name_id.strip() == "")
