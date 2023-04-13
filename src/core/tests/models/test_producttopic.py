from django.core.exceptions import ValidationError
from django.test import TestCase
from model_mommy import mommy


class ProductTopicTestCase(TestCase):

    def test_str(self):
        pt = mommy.make('core.ProductTopic', name='foo')
        self.assertEqual(str(pt), 'foo')

    def test_no_name(self):
        pt = mommy.make('core.ProductTopic')
        pt.name = None
        with self.assertRaises(ValidationError) as cm:
            pt.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['name'])
        self.assertEqual(cm.exception.message_dict['name'], ['This field cannot be null.'])

    def test_blank_name(self):
        pt = mommy.make('core.ProductTopic')
        pt.name = ''
        with self.assertRaises(ValidationError) as cm:
            pt.full_clean()
        self.assertEqual(list(cm.exception.message_dict.keys()), ['name'])
        self.assertEqual(cm.exception.message_dict['name'], ['This field cannot be blank.'])
