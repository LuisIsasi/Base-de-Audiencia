from django.core.exceptions import ValidationError
from django.test import TestCase
from model_mommy import mommy

from core.models import Product


class ProductTestCase(TestCase):

    def test_str(self):
        product = mommy.make(
            'core.Product', slug='foo', name='foo', brand="Govexec", type="event"
        )
        self.assertEqual(str(product), 'foo [event]')

    def test_slug_with_spaces(self):
        slug = 'abc def ghi'
        product_subtype = mommy.make('core.ProductSubtype', name="subtype1")
        product_topic = mommy.make('core.ProductTopic', name="topic1")
        product = mommy.make(
            'core.Product', slug=slug, name='foo', brand="Govexec", type="event",
            subtypes=[product_subtype], topics=[product_topic]
        )
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['slug'])
        self.assertEqual(
            cm.exception.message_dict['slug'],
            ['Product slugs can only contain lowercase letters and/or numbers.']
        )

    def test_slug_with_uc(self):
        slug = 'ABCabc'
        product = mommy.make(
            'core.Product', slug=slug, name='foo', brand="Govexec", type="event"
        )
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['slug'])
        self.assertEqual(
            cm.exception.message_dict['slug'],
            ['Product slugs can only contain lowercase letters and/or numbers.']
        )

    def test_slug_with_punc(self):
        slug = 'a-b-c'
        product = mommy.make(
            'core.Product', slug=slug, name='foo', brand="Govexec", type="event"
        )
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['slug'])
        self.assertEqual(
            cm.exception.message_dict['slug'],
            ['Product slugs can only contain lowercase letters and/or numbers.']
        )

    def test_slug_is_none(self):
        product = mommy.make(
            'core.Product', slug='foo', name='foo', brand="Govexec", type="event"
        )
        product.slug = None
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['slug'])
        self.assertEqual(
            cm.exception.message_dict['slug'],
            ['This field cannot be null.']
        )

    def test_name_is_none(self):
        product = mommy.make('core.Product', slug='foo', brand="Govexec", type="event")
        product.name = None
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['name'])
        self.assertEqual(
            cm.exception.message_dict['name'],
            ['This field cannot be null.']
        )

    def test_name_is_empty_string(self):
        product = mommy.make('core.Product', slug='foo', brand="Govexec", type="event", name='')
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['name'])
        self.assertEqual(
            cm.exception.message_dict['name'],
            ['This field cannot be blank.']
        )

    def test_brand_is_none(self):
        product = mommy.make('core.Product', name='foo', slug='foo', brand="Govexec", type="event")
        product.brand = None
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['brand'])
        self.assertEqual(
            cm.exception.message_dict['brand'],
            ['This field cannot be null.']
        )

    def test_brand_is_empty_string(self):
        product = mommy.make('core.Product', name='foo', slug='foo', brand="", type="event")
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['brand'])
        self.assertEqual(
            cm.exception.message_dict['brand'],
            ['This field cannot be blank.']
        )

    def test_brand_unexpected_value(self):
        product = mommy.make('core.Product', name='foo', slug='foo', brand="Foo", type="event")
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['brand'])
        self.assertEqual(
            cm.exception.message_dict['brand'],
            ["Value 'Foo' is not a valid choice."]
        )

    def test_type_is_none(self):
        product = mommy.make('core.Product', name='foo', slug='foo', brand="Govexec", type="event")
        product.type = None
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['type'])
        self.assertEqual(
            cm.exception.message_dict['type'],
            ['This field cannot be null.']
        )

    def test_type_is_empty_string(self):
        product = mommy.make('core.Product', name='foo', slug='foo', brand="Govexec", type="event")
        product.type = ''
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['type'])
        self.assertEqual(
            cm.exception.message_dict['type'],
            ['This field cannot be blank.']
        )

    def test_type_unexpected_value(self):
        product = mommy.make('core.Product', name='foo', slug='foo', brand="Govexec", type="foo")
        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['type'])
        self.assertEqual(
            cm.exception.message_dict['type'],
            ["Value 'foo' is not a valid choice."]
        )

    def test_registered_verb(self):
        for i, product_type in enumerate([x[0] for x in Product.PRODUCT_TYPE_CHOICES]):
            product = mommy.make(
                'core.Product', name='foo{}'.format(i), slug='foo{}'.format(i),
                brand="Govexec", type=product_type
            )
            self.assertEqual(product.registered_verb, "registered")

    def test_consumed_verb(self):
        for i, product_type in enumerate([x[0] for x in Product.PRODUCT_TYPE_CHOICES]):
            product = mommy.make(
                'core.Product', name='foo{}'.format(i), slug='foo{}'.format(i),
                brand="Govexec", type=product_type
            )
            self.assertNotEqual(product.consumed_verb, None)

    def test_product_create_happy_path(self):
        product_subtype = mommy.make('core.ProductSubtype', name="subtype1")
        product_topic = mommy.make('core.ProductTopic', name="topic1")
        product = mommy.make(
            'core.Product', slug='foo', name='Foo', brand="Govexec", type="event",
            subtypes=[product_subtype], topics=[product_topic]
        )
        product.validate_and_save()
