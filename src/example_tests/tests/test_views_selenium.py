from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from model_mommy import mommy
from selenium import webdriver


class TestQuestionnaireSeleniumTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.q = mommy.make("example_tests.TestQuestionnaire")
        cls.selenium = webdriver.PhantomJS()
        cls.selenium.implicitly_wait(2)  # seconds
        cls.selenium.get(cls.live_server_url + cls.q.get_absolute_url())

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        cls.q.delete()
        super().tearDownClass()

    def test_jquery_loaded(self):
        """
        just thought this was cool. I think you can even do something with what is returned.
        """
        self.selenium.execute_script("return $")

    def test_element_created(self):
        """
        selenium.get will wait until onload event has fired.
        """
        self.selenium.find_element_by_class_name("test-js")
