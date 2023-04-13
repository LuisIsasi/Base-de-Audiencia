from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from ...models import ProductAction


class ProductActionTestCase(TestCase):

    def test_str_representation(self):
        au = mommy.make('core.AudienceUser', email="a@a.com")
        au.validate_and_save()
        product_subtype = mommy.make('core.ProductSubtype', name="subtype1")
        product_topic = mommy.make('core.ProductTopic', name="topic1")
        product = mommy.make(
            'core.Product', slug='foo', name='Foo', brand="Govexec", type="event",
            subtypes=[product_subtype], topics=[product_topic]
        )
        action = au.record_product_action('foo', 'registered', timezone.now())
        self.assertIsInstance(action, ProductAction)
        self.assertEqual(str(action), "{} - {}".format(product.name, 'registered'))
