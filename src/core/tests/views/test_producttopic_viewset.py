from model_mommy import mommy

from rest_framework import status
from rest_framework import test as rest_test


class ProductTopicsViewsetTests(rest_test.APITestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token
        u = User.objects.create(username='test')
        t = Token.objects.create(user=u)
        self.client.force_authenticate(user=u, token=t)

    def test_create_producttopic_missing_payload(self):
        r = self.client.post("/api/product-topics", format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"name": ["This field is required."]})

    def test_create_producttopic_empty_payload(self):
        r = self.client.post("/api/product-topics", {}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"name": ["This field is required."]})

    def test_create_duplicate_producttopic(self):
        r = self.client.post("/api/product-topics", {"name": "foo"}, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.post("/api/product-topics", {"name": "foo"}, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {'name': ['ProductTopic with this name already exists.']})

    def test_producttopic_list(self):
        mommy.make('core.Producttopic', name='foo')
        mommy.make('core.Producttopic', name='bar')

        r = self.client.get("/api/product-topics")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get('count'), 2)
        results = r.json()['results']
        self.assertEqual(len([x for x in results if x['name'] in ('foo', 'bar')]), 2)

    def test_producttopic_list_empty(self):
        r = self.client.get("/api/product-topics")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('results', r.json())

    def test_producttopic_delete(self):
        r = self.client.post("/api/product-topics", {"name": "foo"}, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.delete("/api/product-topics/{}".format(r.json().get('id')), format='json')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_producttopic_update(self):
        r = self.client.post("/api/product-topics", {"name": "foo"}, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.put("/api/product-topics/{}".format(r.json().get('id')), {}, format='json')
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)
