from itertools import chain

from django.core.exceptions import ValidationError

from core import models as core_models


def reserved_words_validator(value):
    reserved_words = {
        "email_domain",
        "external_source",
        "modified_time",
        "name",
        "product_topics",
        "source",
        "source_signup_date",
        "sources",
    }
    reserved_prefixes = chain(
        [x + r"_" for x, _ in core_models.List.LIST_TYPE_CHOICES],
        [x + r"s_" for x, _ in core_models.List.LIST_TYPE_CHOICES],
        [x + r"s_" for x, _ in core_models.Product.PRODUCT_TYPE_CHOICES],
        [x + r"_" for x, _ in core_models.Product.PRODUCT_TYPE_CHOICES],
    )

    reserved_word_msg = "{} is invalid because it matches a reserved word."
    reserved_prefix_msg = "{} is invalid because it matches a reserved prefix: {}."
    if value in reserved_words:
        raise ValidationError(reserved_word_msg.format(value))
    for prefix in reserved_prefixes:
        try:
            if value.startswith(prefix):
                raise ValidationError(reserved_prefix_msg.format(value, prefix))
        except AttributeError:
            raise ValidationError("Value must be a string like object")


def reserved_words_jsonfield_validator(value):
    try:
        keys = value.keys()
    except AttributeError:
        raise ValidationError("Value must provide a `keys` method")
    else:
        for key in keys:
            reserved_words_validator(key)
