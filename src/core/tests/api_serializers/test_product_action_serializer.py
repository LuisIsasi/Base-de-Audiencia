from django.utils import timezone
from django.test import TestCase
from model_mommy import mommy
from rest_framework.exceptions import ValidationError

from core.api_serializers import ProductActionSerializer


"""
We get test coverage for most of our custom rest framework serializer code by dint of
testing the rest API views, but some of the serializer code is not reachable that way,
so we have to add some extra tests here.
"""


class ProductActionSerializerTests(TestCase):
    def test_product_action_bad_audienceuser_pk(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()

        s = ProductActionSerializer(
            data={
                "type": "registered",
                "timestamp": timezone.now().isoformat(),
                "audienceuser_pk": 1,
                "product": "foo",
            }
        )
        with self.assertRaises(ValidationError) as cm:
            s.is_valid(raise_exception=True)
        self.assertEqual(
            cm.exception.detail, {"audience_user": ["This field is required."]}
        )
