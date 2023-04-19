import ast
import json
import re

from django.forms import Widget
from django.template.loader import get_template
from natsort import natsorted
from sailthru_sync.validators import reserved_words_validator as reserved_validator


class DecomposedKeyValueJSONWidget(Widget):
    """
    Custom widget that can be used with `JSONField`s when only flat
    string-based key/value pairs are being used in the JSON object:
    no support for types other than strings, no sequences, no nesting.

    You can use this widget if the JSON you are storing in your `JSONField`
    looks like this:
        {
            "a": "b",
            "c": "d",
            "e": "f"
        }
    """

    add_button_label = "Add a var"
    remove_confirm_prompt_text = "Remove var?"

    field_prefix = "decomposedkeyvaluejsonwidget"

    dupe_key_mangling_token = "_DUPLICATE_VAR_"
    dupe_key_mangling_regex = re.compile(r"^.*{}(\d+)".format(dupe_key_mangling_token))

    template_path = "widgets/decomposed-key-value-json-widget.html"

    class Media:
        css = {"all": ("core/admin/css/decomposed-key-value-json-widget.css",)}
        js = ("core/admin/js/decomposed-key-value-json-widget.js",)

    def render(self, name, value, attrs=None):
        # this is a bad hack to deal with a bug in Django 1.9 -- see:
        # https://code.djangoproject.com/ticket/25532
        # TODO once that ^ bug has been fixed, remove this 'if' block and re-test
        # that round-tripping the vars when there are ValidationErrors on the
        # vars field doesn't break the JSON encoding, as it does now
        if value and (not value.startswith("{")):
            value = ast.literal_eval(value)

        pairs = json.loads(value) if value else {}
        rows = []

        for i, k in enumerate(natsorted(pairs.keys())):
            # these are sanity checks, shouldn't actually ever be raised
            if not isinstance(pairs[k], type(str())):
                raise TypeError("Expected a string.")

            val = pairs[k]

            duplicate_key = self.dupe_key_mangling_regex.match(k)
            if duplicate_key:
                k = k.split(self.dupe_key_mangling_token)[0]
            try:
                is_reserved = False
                reserved_validator(k)
            except:
                is_reserved = True

            has_spaces = len(k.split()) > 1

            has_error = is_reserved or has_spaces or duplicate_key
            rows.append(
                {
                    "key": k,
                    "val": val,
                    "pair_id": str(i),
                    "duplicate_key": duplicate_key,
                    "has_spaces": has_spaces,
                    "is_reserved": is_reserved,
                    "has_error": has_error,
                }
            )

        template = get_template(self.template_path)
        return template.render(
            {
                "rows": rows,
                "field": name,
                "prefix": self.field_prefix,
                "add_button_label": self.add_button_label,
                "remove_confirm_prompt_text": self.remove_confirm_prompt_text,
            }
        )

    def value_from_datadict(self, data, files, name):
        pair_ids = sorted(
            list(
                set(
                    [
                        x.split("_")[-1][1:-1]
                        for x in data.keys()
                        if x.startswith("{}_".format(self.field_prefix))
                    ]
                )
            )
        )

        ret = {}

        for pid in pair_ids:
            pair_keys = data.getlist("{}_key_[{}]".format(self.field_prefix, pid))
            pair_values = data.getlist("{}_value_[{}]".format(self.field_prefix, pid))
            assert len(pair_keys) == 1
            assert len(pair_values) == 1
            if pair_keys[0] and pair_keys[0].strip():
                k = pair_keys[0].strip()
                if k in ret:
                    k = self.mangle_duplicate_dict_key(k, ret)
                ret[k] = pair_values[0].strip()

        return json.dumps(ret)

    def mangle_duplicate_dict_key(self, k, d):
        # this is a clumsy way to handle duplicate keys, and maybe it would
        # have been better to do it on the front-end (by adding some JS to
        # the Django admin) -- and then raise an exception if somehow duplicates
        # bypassed the front-end on-submit checks -- but we weren't seeing an
        # easy way to do it that way, so we ended up with this solution
        # TODO does anyone know how to add on-submit validation to Django
        #      Admin change views? They do something weird with their forms
        #      and I didn't want to spend any more time trying to figure it out.
        r = self.dupe_key_mangling_regex
        existing_keys = sorted([int(r.findall(x)[0]) for x in d.keys() if r.findall(x)])
        next_number = (existing_keys[-1] + 1) if existing_keys else 1
        new_key = "{}{}{}".format(k, self.dupe_key_mangling_token, next_number)
        assert new_key not in d, "this method does not work as expected"
        return new_key
