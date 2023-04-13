from bs4 import BeautifulSoup
from django import test
from django.contrib.admin.sites import AdminSite
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.urlresolvers import reverse
from model_mommy import mommy
from selenium import webdriver
from selenium.webdriver.support.ui import Select

from ... import admin as core_admin, models as core_models


@test.override_settings(SAILTHRU_SYNC_SIGNALS_ENABLED=False, RAVEN_CONFIG={'dsn': None})
class ProductAdminTest(test.TestCase):

    def setUp(self):
        self.admin = core_admin.ProductAdmin(core_models.Product, AdminSite)
        self.superuser = mommy.make(
            'auth.User',
            username='foo',
            email="a@a.com",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.superuser)

    def test_changelist_view(self):
        qs = "_popup=external"
        changelist_url = reverse("admin:core_product_changelist")
        add_url = reverse("admin:core_product_add")

        response = self.client.get(changelist_url + "?" + qs)
        soup = BeautifulSoup(response.content, 'html5lib')
        link = soup.select(".addlink")
        self.assertEqual(len(link), 1)
        self.assertEqual(link[0]["href"], add_url + "?" + qs)

    def test_fieldsets(self):
        product = mommy.make(
            'core.Product',
            slug='foo',
            name='foo',
            brand="Govexec",
            type="event"
        )

        request = None
        fieldsets = self.admin.get_fieldsets(request, None)
        self.assertEqual(self.admin.add_fieldsets, fieldsets)

        fieldsets = self.admin.get_fieldsets(request, product)
        self.assertEqual(self.admin.change_fieldsets, fieldsets)

    def test_list_display(self):
        qs = "_popup=external"
        url = reverse("admin:core_product_changelist")

        response = self.client.get(url)
        list_display = self.admin.get_list_display(response.wsgi_request)
        self.assertEqual(self.admin.list_display, list_display)

        response = self.client.get(url + "?" + qs)
        list_display = self.admin.get_list_display(response.wsgi_request)
        self.assertEqual(self.admin.list_display_external_popup, list_display)

    def test_list_display_links(self):
        qs = "_popup=external"
        url = reverse("admin:core_product_changelist")

        response = self.client.get(url)
        list_display = self.admin.get_list_display(response.wsgi_request)

        list_display_links = self.admin.get_list_display_links(response.wsgi_request, list_display)
        self.assertEqual(list_display[0], list_display_links[0])

        response = self.client.get(url + "?" + qs)
        list_display_links = self.admin.get_list_display_links(response.wsgi_request, list_display)
        self.assertEqual(None, list_display_links)

    def test_get_for_external_popup_name(self):
        product = mommy.make(
            'core.Product',
            slug='foo',
            name='bar',
            brand="Govexec",
            type="event"
        )

        markup = self.admin.get_for_external_popup_name(product)
        for_soup = """
            <html><body>{}</body></html>
        """.format(markup)
        soup = BeautifulSoup(for_soup, 'html5lib')
        tags = soup.select(".for-external-popup-core-products-name")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["data-name"], product.name)
        self.assertEqual(tags[0]["data-slug"], product.slug)

    def test_readonly_fields(self):
        product = mommy.make(
            'core.Product',
            slug='foo',
            name='bar',
            brand="Govexec",
            type="event"
        )
        request = None  # doesn't matter here
        readonly_fields = self.admin.get_readonly_fields(request, None)
        self.assertEqual(self.admin.readonly_fields, readonly_fields)

        extra = ('type', 'slug', 'csv_columns_html', 'sailthru_vars_html',)
        readonly_fields = self.admin.get_readonly_fields(request, product)
        self.assertEqual(self.admin.readonly_fields + extra, readonly_fields)

    def test_is_external_popup(self):
        product = mommy.make(
            'core.Product',
            slug='foo',
            name='bar',
            brand="Govexec",
            type="event"
        )
        qs = "_popup=external"
        url = reverse("admin:core_product_changelist")
        response = self.client.get(url)
        self.assertFalse(self.admin.is_external_popup(response.wsgi_request))
        response = self.client.post(url)
        self.assertFalse(self.admin.is_external_popup(response.wsgi_request))

        response = self.client.get(url + "?" + qs)
        self.assertTrue(self.admin.is_external_popup(response.wsgi_request))
        response = self.client.post(url + "?" + qs)
        self.assertTrue(self.admin.is_external_popup(response.wsgi_request))

    def test_response_add(self):
        product = mommy.make(
            'core.Product',
            slug='foo',
            name='bar',
            brand="Govexec",
            type="event"
        )

        qs = "_popup=external"
        url = reverse("admin:core_product_add")
        request = test.RequestFactory().get(url + "?" + qs)

        response = self.admin.response_add(request, product)
        response.render()
        soup = BeautifulSoup(response.content, 'html5lib')
        scripts = soup.body.find_all("script")

        js = scripts[1].text.strip()
        expected_js =  'AUDB.send_products_selection("{}", "{}");'.format(
            product.slug, product.name
        )
        self.assertEqual(js, expected_js)


class TestQuestionnaireSeleniumTestCase(StaticLiveServerTestCase):

    def setUp(self):
        self.selenium = webdriver.PhantomJS()
        self.selenium.implicitly_wait(2)  # seconds

        self.superuser = mommy.make(
            'auth.User',
            username='foo',
            email="a@a.com",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.superuser)
        self.cookie = self.client.cookies["sessionid"]
        self.selenium.get(self.live_server_url + reverse("admin:core_product_add"))
        self.selenium.add_cookie({
            'name': 'sessionid',
            'value': self.cookie.value,
            'secure': False,
            'path': '/',
            'domain': '127.0.0.1',
        })
        self.selenium.refresh()

    def tearDown(self):
        self.selenium.quit()

    def test_message_prod_origins(self):
        product_subtype = mommy.make('core.ProductSubtype', name="subtype1")
        product_topic = mommy.make('core.ProductTopic', name="topic1")

        self.selenium.get(self.live_server_url + reverse("admin:core_product_add") + "?_popup=external")
        name = self.selenium.find_element_by_id("id_name")
        name.send_keys("name")

        slug = self.selenium.find_element_by_id("id_slug")
        slug.send_keys("slug")

        type_ = Select(self.selenium.find_element_by_id("id_type"))
        type_.select_by_value("asset")

        brand = Select(self.selenium.find_element_by_id("id_brand"))
        brand.select_by_value("Govexec")

        subtypes = Select(self.selenium.find_element_by_id("id_subtypes"))
        subtypes.select_by_visible_text("subtype1")

        topics = Select(self.selenium.find_element_by_id("id_topics"))
        topics.select_by_visible_text("topic1")

        save = self.selenium.find_element_by_name("_save")
        save.click()
        self.assertEqual(self.selenium.title, "Popup closing...")
        script = "return AUDB.valid_message_origins.test('https://admin.govexec.com');"
        self.assertTrue(self.selenium.execute_script(script))
