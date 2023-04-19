from bs4 import BeautifulSoup
from django import test
from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import reverse
from model_mommy import mommy

from ... import admin as core_admin, models as core_models


@test.override_settings(SAILTHRU_SYNC_SIGNALS_ENABLED=False, RAVEN_CONFIG={"dsn": None})
class ListAdminTest(test.TestCase):
    def setUp(self):
        self.factory = test.RequestFactory()
        self.admin = core_admin.ListAdmin(core_models.List, AdminSite)

    def test_zephyr_optout_code(self):

        list_instance = mommy.make(
            "core.List",
            slug="newsletter_my_newsletter",
            name="my newsletter",
            type="newsletter",
        )
        code = self.admin.zephyr_optout_code(list_instance)

        soup = BeautifulSoup(code, "html5lib")

        btn = soup.find_all(class_="core-list-zephyr-copy-btn")
        code = soup.find_all(class_="core-list-zephyr-code")

        self.assertEqual(len(btn), 1)
        self.assertEqual(len(code), 1)

        self.assertIn("data-clipboard-text", btn[0].attrs)

        code_string = ""
        for node in code[0].contents:
            try:
                node.contents
            except AttributeError:
                code_string += str(node).strip()

        self.assertFalse(code_string == "")

        clipboard_code = btn[0].attrs["data-clipboard-text"]

        self.assertEqual(code_string, clipboard_code)

        self.assertTrue(code_string.startswith("{optout_confirm_url + '&amp;"))

    def test_fieldsets(self):
        list_ = mommy.make(
            "core.List",
            slug="newsletter_my_newsletter",
            name="my newsletter",
            type="newsletter",
        )
        url = reverse("admin:core_list_change", args=(list_.pk,))
        request = self.factory.get(url)

        fieldsets = self.admin.get_fieldsets(request, None)
        self.assertEqual(self.admin.add_fieldsets, fieldsets)

        fieldsets = self.admin.get_fieldsets(request, list_)
        self.assertEqual(self.admin.change_fieldsets, fieldsets)

    def test_readonly_fields(self):
        list_ = mommy.make(
            "core.List",
            slug="newsletter_my_newsletter",
            name="my newsletter",
            type="newsletter",
        )
        url = reverse("admin:core_list_change", args=(list_.pk,))
        request = self.factory.get(url)

        fields = self.admin.get_readonly_fields(request, None)
        self.assertEqual(self.admin.readonly_fields, fields)
        self.assertNotIn("zephyr_optout_code", fields)

        fields = self.admin.get_readonly_fields(request, list_)
        self.assertIn("zephyr_optout_code", fields)
