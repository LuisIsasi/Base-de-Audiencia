from model_mommy import mommy

from rest_framework import status
from rest_framework import test as rest_test


class ProductViewsetTests(rest_test.APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token

        u = User.objects.create(username="test")
        t = Token.objects.create(user=u)
        self.client.force_authenticate(user=u, token=t)

    def test_create_product_missing_payload(self):
        r = self.client.post("/api/products", format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "subtypes": ["Must provide one or most product subtypes."],
                "brand": ["This field is required."],
                "name": ["This field is required."],
                "slug": ["This field is required."],
                "type": ["This field is required."],
                "topics": ["Must provide one or most product topics."],
            },
        )

    def test_create_product_empty_payload(self):
        r = self.client.post("/api/products", {}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "subtypes": ["This field is required."],
                "brand": ["This field is required."],
                "name": ["This field is required."],
                "slug": ["This field is required."],
                "type": ["This field is required."],
                "topics": ["This field is required."],
            },
        )

    def test_create_product_slug_with_spaces(self):
        payload = {"slug": "a b c"}
        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json().get("slug", []),
            ["Product slugs can only contain lowercase letters and/or numbers."],
        )

    def test_create_product_slug_with_uppercase(self):
        payload = {"slug": "abcABC"}
        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json().get("slug", []),
            ["Product slugs can only contain lowercase letters and/or numbers."],
        )

    def test_create_product_slug_with_punc(self):
        payload = {"slug": "a-b-c"}
        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json().get("slug", []),
            ["Product slugs can only contain lowercase letters and/or numbers."],
        )

    def test_create_product_bad_brand(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "foo",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"brand": ['"foo" is not a valid choice.']})

    def test_create_product_bad_type(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")

        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "foo",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"type": ['"foo" is not a valid choice.']})

    def test_create_product_bad_topic(self):
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"topics": ["Unknown product topic: topic1"]})

    def test_create_product_malformed_topic(self):
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": [{}],
            "subtypes": [{"name": "subtype1"}],
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"topics": ['Must specify "name".']})

    def test_create_product_bad_subtype(self):
        mommy.make("core.ProductTopic", name="topic1")
        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"subtypes": ["Unknown product subtype: subtype1"]})

    def test_create_product_malformed_subtype(self):
        mommy.make("core.ProductTopic", name="topic1")
        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{}],
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"subtypes": ['Must specify "name".']})

    def test_create_product_multiple_topics(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductTopic", name="topic2")
        mommy.make("core.ProductSubtype", name="subtype1")

        topics = [{"name": "topic1"}, {"name": "topic2"}]
        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": topics,
            "subtypes": [{"name": "subtype1"}],
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.get("/api/products/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["topics"], topics)

    def test_create_product_multiple_subtypes(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        mommy.make("core.ProductSubtype", name="subtype2")

        subtypes = [{"name": "subtype1"}, {"name": "subtype2"}]
        payload = {
            "slug": "foo123",
            "brand": "Govexec",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": subtypes,
            "type": "event",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.get("/api/products/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["subtypes"], subtypes)

    def test_product_repr(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Nextgov",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "asset",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        product_id = r.json().get("id")
        self.assertNotEqual(product_id, None)

        r = self.client.get("/api/products/{}".format(product_id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        product_repr = r.json()
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(product_repr["name"], "foo 123")
        self.assertEqual(product_repr["slug"], "foo123")
        self.assertEqual(product_repr["brand"], "Nextgov")
        self.assertEqual(product_repr["type"], "asset")
        self.assertEqual(product_repr["subtypes"], [{"name": "subtype1"}])
        self.assertEqual(product_repr["topics"], [{"name": "topic1"}])

        self.assertEqual(
            sorted(r.json().keys()),
            sorted(
                [
                    "id",
                    "name",
                    "slug",
                    "brand",
                    "type",
                    "subtypes",
                    "topics",
                    "consumed_verb",
                    "registered_verb",
                ]
            ),
        )

    def test_create_duplicate_product(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Nextgov",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "asset",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "slug": ["This field must be unique."],
                "name": ["Product with this name already exists."],
            },
        )

    def test_product_list_empty(self):
        r = self.client.get("/api/products")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("results", r.json())
        self.assertEqual(r.json()["results"], [])

    def test_product_list_with_results(self):
        mommy.make(
            "core.Product", slug="foo", name="foo", type="event", brand="Govexec"
        )
        mommy.make(
            "core.Product", slug="bar", name="bar", type="event", brand="Govexec"
        )

        r = self.client.get("/api/products")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 2)
        results = r.json()["results"]
        self.assertEqual(len([x for x in results if x["slug"] in ("foo", "bar")]), 2)

    def test_product_delete(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Nextgov",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "asset",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.delete("/api/products/{}".format(r.json().get("id")))
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_product_update(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Nextgov",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "asset",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.put(
            "/api/products/{}".format(r.json().get("id")), {}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_product_find_by_slug(self):
        mommy.make("core.ProductTopic", name="topic1")
        mommy.make("core.ProductSubtype", name="subtype1")
        payload = {
            "slug": "foo123",
            "brand": "Nextgov",
            "name": "foo 123",
            "topics": [{"name": "topic1"}],
            "subtypes": [{"name": "subtype1"}],
            "type": "asset",
        }

        r = self.client.post("/api/products", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.get("/api/products", {"slug": payload["slug"]})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
