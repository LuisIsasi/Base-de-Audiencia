from django.test import TestCase
from model_mommy import mommy
from rest_framework.exceptions import ValidationError

from core.api_serializers import SubscriptionTriggerSerializer


"""
We get test coverage for most of our custom rest framework serializer code by dint of
testing the rest API views, but some of the serializer code is not reachable that way,
so we have to add some extra tests here.
"""


class SubscriptionTriggerSerializerTests(TestCase):
    def test_missing_primary_list_slug(self):
        s = SubscriptionTriggerSerializer(data={"related_list_slug": "foo"})
        with self.assertRaises(ValidationError) as cm:
            s.is_valid(raise_exception=True)
        self.assertEqual(
            cm.exception.detail, {"primary_list_slug": "This field is required."}
        )

    def test_unknown_primary_list_slug(self):
        mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        s = SubscriptionTriggerSerializer(
            data={
                "related_list_slug": "foo",
                "primary_list_slug": "bar",
                "override_previous_unsubscribes": True,
            }
        )
        with self.assertRaises(ValidationError) as cm:
            s.is_valid(raise_exception=True)
        self.assertEqual(
            cm.exception.detail, {"primary_list_slug": "Primary list does not exist."}
        )

    def test_happy_path(self):
        list_foo = mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="bar", slug="bar", type="newsletter")
        data = {
            "related_list_slug": "foo",
            "primary_list_slug": "bar",
            "override_previous_unsubscribes": True,
        }
        s = SubscriptionTriggerSerializer()
        self.assertEqual(
            s.to_internal_value(data=data),
            {
                "related_list": list_foo,
                "primary_list": list_bar,
                "override_previous_unsubscribes": True,
            },
        )
