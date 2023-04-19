import re

from django.core import validators as django_validators
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models


list_slug_validator = django_validators.RegexValidator(
    re.compile(r"^[a-z0-9_]+\Z"),
    (
        "List/newsletter slugs can only contain: lowercase letters, numbers, underscores."
    ),
    "invalid",
)


product_slug_validator = django_validators.RegexValidator(
    re.compile(r"^[a-z0-9]+$"),
    ("Product slugs can only contain lowercase letters and/or numbers."),
    "invalid",
)


def normalized_email_validator(value):
    if value and value.lower() != value:
        raise ValidationError("Email addresses must be lowercase.")


def vars_jsonfield_validator(value):
    if not isinstance(value, type(dict())):
        raise ValidationError("This field must be a dictionary.")
    if [k for k in list(value.keys()) if not isinstance(k, type(str()))]:
        raise ValidationError("All var keys must be strings.")
    if [v for v in list(value.values()) if not isinstance(v, type(str()))]:
        raise ValidationError("All var values must be strings.")
    if [k for k in list(value.keys()) if len(k.split()) > 1]:
        raise ValidationError("Var keys may not contains spaces.")


def varkey_validator(value):
    if value and len(value.split()) > 1:
        raise ValidationError("Vars may not contains spaces.")


class ReferrerField(models.URLField):
    """
    Intended to make `referrer` more inclusive.
    See also `core.api_serializers.ReferrerField`.
    """

    default_validators = [
        URLValidator(
            schemes=[
                "http",
                "https",
                "android-app",
            ]
        )
    ]


class ProductSlugField(models.CharField):
    description = (
        "Extends SlugField to enforce lower-alpha-numeric slugs with no punctuation."
    )
    validators = [product_slug_validator]


class ListSlugField(models.CharField):
    description = "Extends SlugField to enforce snake-case-style slugs, eg 'my_slug'."
    validators = [list_slug_validator]


class NormalizedEmailField(models.EmailField):
    description = (
        "Extends EmailField to enforce all-lowercase and whitespace stripping."
    )
    validators = [django_validators.validate_email, normalized_email_validator]

    def pre_save(self, model_instance, add):
        field_value = super(NormalizedEmailField, self).pre_save(model_instance, add)
        field_value = field_value.strip() if field_value else field_value
        return field_value
