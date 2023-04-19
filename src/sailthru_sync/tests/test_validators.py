from itertools import chain
from django.core.exceptions import ValidationError
from django.test import TestCase

from core import models as core_models

from ..validators import reserved_words_jsonfield_validator


class ReservedWordsTestCase(TestCase):
    def test_validate_reserved_words(self):
        reserved_words = (
            "email_domain",
            "external_source",
            "modified_time",
            "name",
            "product_topics",
            "source",
            "source_signup_date",
            "sources",
        )
        fail = list(
            chain(
                reserved_words,
                [x + r"_" for x, _ in core_models.List.LIST_TYPE_CHOICES],
                [x + r"s_" for x, _ in core_models.List.LIST_TYPE_CHOICES],
                [x + r"_" for x, _ in core_models.Product.PRODUCT_TYPE_CHOICES],
                [x + r"s_" for x, _ in core_models.Product.PRODUCT_TYPE_CHOICES],
            )
        )
        with self.assertRaises(ValidationError):
            reserved_words_jsonfield_validator(dict(zip(fail, fail)))
        passes = []
        for x in reserved_words:
            passes.append(x + "junk")
            passes.append("asdasfd" + x)
            passes.append(" {} ".format(x))
        passes = list(
            chain(
                passes,
                [x for x, _ in core_models.List.LIST_TYPE_CHOICES],
                [x for x, _ in core_models.List.LIST_TYPE_CHOICES],
                [x for x, _ in core_models.Product.PRODUCT_TYPE_CHOICES],
                [x for x, _ in core_models.Product.PRODUCT_TYPE_CHOICES],
            )
        )
        reserved_words_jsonfield_validator(dict(zip(passes, passes)))
