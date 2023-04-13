import json
from bs4 import BeautifulSoup
from urllib.parse import urlencode

from django.http.request import QueryDict
from django.test import SimpleTestCase

from .. import widgets


class DecomposedKeyValueJSONWidgetTest(SimpleTestCase):
    widget = widgets.DecomposedKeyValueJSONWidget()


    def to_querydict_key(self, key):
        new_key = "{}_key_[{}]".format(self.widget.field_prefix, key)
        return new_key

    def to_querydict_value(self, value):
        new_value = "{}_value_[{}]".format(self.widget.field_prefix, value)
        return new_value

    def test_mangle_duplicate_dict_key(self):
        mangled = self.widget.mangle_duplicate_dict_key('', {})
        self.assertEquals(mangled, self.widget.dupe_key_mangling_token + '1')

        test_key = self.widget.dupe_key_mangling_token + '1'
        mangled = self.widget.mangle_duplicate_dict_key('', {test_key: ''})
        self.assertEquals(mangled, self.widget.dupe_key_mangling_token + '2')

        test_dict = {
            self.widget.dupe_key_mangling_token + '2': '',
            self.widget.dupe_key_mangling_token + '1': '',
            self.widget.dupe_key_mangling_token + '4': '',
        }
        mangled = self.widget.mangle_duplicate_dict_key('', test_dict)
        self.assertEquals(mangled, self.widget.dupe_key_mangling_token + '5')

    def test_value_from_datadict(self):
        value = self.widget.value_from_datadict({}, "Doesn't matter", "Doesn't matter")
        self.assertEquals(value, "{}")

        encoded = urlencode({
            self.to_querydict_key("a-1"): "b",
            self.to_querydict_value("a-1"): "",
            self.to_querydict_key("a-2"): "b",
            self.to_querydict_value("a-2"): "",
        })
        test_dict = QueryDict(encoded)
        value = self.widget.value_from_datadict(test_dict, "Doesn't matter", "Doesn't matter")
        value_dict = json.loads(value)
        self.assertIn("b", value_dict)
        self.assertIn("b" + self.widget.dupe_key_mangling_token + '1', value_dict)

    def test_render(self):
        test_value = json.dumps({
            'a': '',
        })
        rendered = self.widget.render(name="vars", value=test_value)
        soup = BeautifulSoup(rendered, 'html5lib')
        errors = soup.find_all(class_="jsonwidget-kv-container-error-marker")
        self.assertEqual(len(errors), 0)

    def test_render_sanity(self):
        test_value = json.dumps({
            'a': 1
        })
        with self.assertRaises(TypeError):
            rendered = self.widget.render(name="vars", value=test_value)

        rendered = self.widget.render(name="vars", value='"{}"')

    def test_render_errors(self):
        test_value = json.dumps({
            'a': '',
            'a' + self.widget.dupe_key_mangling_token + '1': '',
            'has spaces': 'asdf',
            'asset_is_reserved': 'asdf',
        })
        rendered = self.widget.render(name="vars", value=test_value)
        soup = BeautifulSoup(rendered, 'html5lib')
        errors = soup.find_all(class_="jsonwidget-kv-container-error-marker")
        self.assertEqual(len(errors), 3)
        msgs = set()
        for error in errors:
            msgs.add(error.text.lower())
        self.assertEqual(msgs, {"duplicate key", "has spaces", "reserved"})
