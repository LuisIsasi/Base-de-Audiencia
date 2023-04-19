from model_mommy import mommy

from rest_framework import status
from rest_framework import test as rest_test


class ListViewsetTests(rest_test.APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token

        u = User.objects.create(username="test")
        t = Token.objects.create(user=u)
        self.client.force_authenticate(user=u, token=t)

    def test_list_list_view(self):
        r = self.client.get("/api/lists")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("results", r.json())

    def test_create_list_missing_payload(self):
        r = self.client.post("/api/lists", format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "slug": ["This field is required."],
                "type": ["This field is required."],
                "name": ["This field is required."],
            },
        )

    def test_create_list_empty_payload(self):
        r = self.client.post("/api/lists", {}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "slug": ["This field is required."],
                "type": ["This field is required."],
                "name": ["This field is required."],
            },
        )

    def test_create_list_bad_slug_upper(self):
        payload = {"type": "newsletter", "name": "foo", "slug": "AAAAAA"}
        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "slug": [
                    "List/newsletter slugs can only contain: "
                    "lowercase letters, numbers, underscores."
                ]
            },
        )

    def test_create_list_bad_slug_spaces(self):
        payload = {"type": "newsletter", "name": "foo", "slug": "a b"}
        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "slug": [
                    "List/newsletter slugs can only contain: "
                    "lowercase letters, numbers, underscores."
                ]
            },
        )

    def test_create_list(self):
        payload = {"type": "newsletter", "name": "foo", "slug": "foo"}
        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        list_id = r.json().get("id")
        self.assertNotEqual(list_id, None)

        r = self.client.get("/api/lists/{}".format(list_id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["name"], "foo")

    def test_list_repr(self):
        payload = {"type": "newsletter", "name": "foo", "slug": "foo"}
        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        list_id = r.json().get("id")
        self.assertNotEqual(list_id, None)

        r = self.client.get("/api/lists/{}".format(list_id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["name"], "foo")
        self.assertEqual(r.json().get("sync_externally"), True)
        self.assertEqual(
            sorted(r.json().keys()),
            sorted(
                [
                    "modified",
                    "id",
                    "type",
                    "sync_externally",
                    "created",
                    "slug",
                    "archived",
                    "subscription_triggers",
                    "name",
                ]
            ),
        )

    def test_create_duplicate_list(self):
        payload = {"type": "newsletter", "name": "foo", "slug": "foo"}
        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "slug": ["This field must be unique."],
                "name": ["List with this name already exists."],
            },
        )

    def test_list_list_filtering(self):
        mommy.make("core.List", slug="foo", name="foo", type="newsletter")
        mommy.make("core.List", slug="bar", name="bar", type="newsletter")
        mommy.make("core.List", slug="baz", name="baz", type="list")

        r = self.client.get("/api/lists")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 3)

        r = self.client.get("/api/lists", {"type": "newsletter"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 2)

        r = self.client.get("/api/lists", {"type": "list"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 1)

        r = self.client.get("/api/lists", {"type": "foo"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 0)

        r = self.client.get("/api/lists", {"slug": "baz"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 1)

        r = self.client.get("/api/lists", {"slug": "f00"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 0)

    def test_list_delete(self):
        payload = {"type": "newsletter", "name": "foo", "slug": "foo"}
        r = self.client.post("/api/lists", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.delete("/api/lists/{}".format(r.json().get("id")))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
