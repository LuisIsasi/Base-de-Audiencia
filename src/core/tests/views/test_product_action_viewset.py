import time

from django.utils import timezone
from model_mommy import mommy
from rest_framework import status
from rest_framework import test as rest_test
import isodate


class ProductActionViewsetTests(rest_test.APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token

        u = User.objects.create(username="test")
        t = Token.objects.create(user=u)
        self.client.force_authenticate(user=u, token=t)

    def test_product_action_missing_payload(self):
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

        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "product": ["This field is required."],
                "timestamp": ["This field is required."],
                "type": ["This field is required."],
            },
        )

    def test_product_action_empty_payload(self):
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

        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk), {}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "product": ["This field is required."],
                "timestamp": ["This field is required."],
                "type": ["This field is required."],
            },
        )

    def test_product_action_bad_product_slug(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "foo",
            "type": "consumed",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"product": ["Product does not exist: foo"]})

    def test_product_action_bad_type(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "bar",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"type": ['"bar" is not a valid choice.']})

    def test_product_action_bad_timestamp(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {"product": "product1", "type": "registered", "timestamp": "foobar"}

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "timestamp": [
                    "Datetime has wrong format. Use one of these formats instead: "
                    "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ]
            },
        )

    def test_create_product_action_happy_path(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        response = r.json()
        self.assertEqual(
            sorted(response.keys()),
            sorted(
                ["details", "created", "id", "timestamp", "product", "modified", "type"]
            ),
        )
        self.assertEqual(response["product"]["id"], product.pk)
        self.assertEqual(response["details"], [])
        self.assertEqual(response["type"], "registered")

    def test_create_product_action_happy_path_with_details(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
            "details": ["details1"],
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        response = r.json()
        self.assertEqual(
            sorted(response.keys()),
            sorted(
                ["details", "created", "id", "timestamp", "product", "modified", "type"]
            ),
        )
        self.assertEqual(response["product"]["id"], product.pk)
        self.assertEqual(response["details"][0]["description"], "details1")
        self.assertEqual(response["type"], "registered")

    def test_create_product_action_bad_type(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": 1,
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"type": ['"1" is not a valid choice.']})

    def test_create_product_action_with_bad_details(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
            "details": "foo",
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"details": ["Expected a list."]})

    def test_create_product_action_happy_path_with_multiple_details(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
            "details": ["details1", "details2"],
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        response = r.json()
        self.assertEqual(
            sorted(response.keys()),
            sorted(
                ["details", "created", "id", "timestamp", "product", "modified", "type"]
            ),
        )
        self.assertEqual(response["product"]["id"], product.pk)
        self.assertEqual(len(response["details"]), 2)
        self.assertEqual(
            [x["description"] for x in response["details"]], ["details2", "details1"]
        )
        self.assertEqual(response["type"], "registered")

    def test_create_and_update_product_action(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        original_response = r.json()[0]

        time.sleep(0.1)
        update_timestamp = timezone.now().isoformat()
        update_payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": update_timestamp,
            "details": ["details1"],
        }
        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            update_payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        update_response = r.json()[0]

        self.assertEqual(original_response["created"], update_response["created"])
        self.assertNotEqual(original_response["created"], update_response["modified"])
        self.assertEqual(original_response["timestamp"], update_response["timestamp"])
        self.assertEqual(update_response["details"][0]["description"], "details1")
        self.assertEqual(
            isodate.parse_datetime(update_response["details"][0]["timestamp"]),
            isodate.parse_datetime(update_timestamp),
        )
        self.assertEqual(original_response["id"], update_response["id"])

    def test_create_and_update_product_action_twice(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        original_response = r.json()[0]

        time.sleep(0.1)
        update_timestamp = timezone.now().isoformat()
        update_payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": update_timestamp,
            "details": ["details1"],
        }
        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            update_payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        update_response = r.json()[0]

        self.assertEqual(original_response["created"], update_response["created"])
        self.assertNotEqual(original_response["created"], update_response["modified"])
        self.assertEqual(original_response["timestamp"], update_response["timestamp"])
        self.assertEqual(update_response["details"][0]["description"], "details1")
        self.assertEqual(
            isodate.parse_datetime(update_response["details"][0]["timestamp"]),
            isodate.parse_datetime(update_timestamp),
        )
        self.assertEqual(original_response["id"], update_response["id"])

        time.sleep(0.1)
        second_update_timestamp = timezone.now().isoformat()
        update_payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": second_update_timestamp,
            "details": ["details2"],
        }
        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            update_payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        update_response = r.json()[0]

        self.assertEqual(original_response["id"], update_response["id"])
        self.assertEqual(original_response["created"], update_response["created"])
        self.assertNotEqual(original_response["created"], update_response["modified"])
        self.assertEqual(original_response["timestamp"], update_response["timestamp"])
        self.assertEqual(update_response["details"][0]["description"], "details2")
        self.assertEqual(update_response["details"][1]["description"], "details1")
        self.assertEqual(
            isodate.parse_datetime(update_response["details"][1]["timestamp"]),
            isodate.parse_datetime(update_timestamp),
        )
        self.assertEqual(
            isodate.parse_datetime(update_response["details"][0]["timestamp"]),
            isodate.parse_datetime(second_update_timestamp),
        )

    def test_create_product_action_get(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        response = r.json()

        r = self.client.get(
            "/api/audience-users/{}/product-actions/{}".format(au.pk, r.json()["id"])
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["id"], response["id"])

    def test_product_action_get_unknown_action(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        r = self.client.get("/api/audience-users/{}/product-actions/1".format(au.pk))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_action_put(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.put(
            "/api/audience-users/{}/product-actions/{}".format(au.pk, r.json()["id"])
        )
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_product_action_patch(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.patch(
            "/api/audience-users/{}/product-actions/{}".format(au.pk, r.json()["id"])
        )
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_product_action_delete(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.delete(
            "/api/audience-users/{}/product-actions/{}".format(
                au.pk, r.json()["id"]
            ).format(r.json().get("id"))
        )
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_product_action_list_empty(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()
        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [])

    def test_product_action_list_for_unknown_user(self):
        r = self.client.get("/api/audience-users/1/product-actions")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_action_list_with_results(self):
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        product = mommy.make(
            "core.Product",
            slug="product1",
            name="Product 1",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        product.validate_and_save()
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.validate_and_save()

        payload = {
            "product": "product1",
            "type": "registered",
            "timestamp": timezone.now().isoformat(),
        }

        r = self.client.post(
            "/api/audience-users/{}/product-actions".format(au.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.get(
            "/api/audience-users/{}/product-actions/{}".format(au.pk, r.json()["id"])
        )
        product_action = r.json()

        r = self.client.get("/api/audience-users/{}/product-actions".format(au.pk))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r_list = r.json()
        self.assertEqual(len(r_list), 1)
        self.assertEqual(r_list[0], product_action)
