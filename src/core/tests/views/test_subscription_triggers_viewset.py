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

    def test_subtrig_list_view_for_unknown_list(self):
        r = self.client.get("/api/lists/1/subscription-triggers")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(r.json(), {"detail": "Not found."})

    def test_subtrig_list_view_empty(self):
        list_ = mommy.make("core.List", name="foo", slug="foo", type="newsletter")

        r = self.client.get("/api/lists/{}/subscription-triggers".format(list_.pk))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [])

    def test_subtrig_create_missing_payload(self):
        list_ = mommy.make("core.List", name="foo", slug="foo", type="newsletter")

        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_.pk), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.json(), {"related_list_slug": "This field is required."})

    def test_subtrig_create_with_missing_override_field(self):
        list_1 = mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        mommy.make("core.List", name="foo2", slug="foo2", type="newsletter")

        payload = {"related_list_slug": "foo2"}
        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_1.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(), {"override_previous_unsubscribes": "This field is required."}
        )

    def test_subtrig_create_with_bad_override_field(self):
        list_1 = mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        mommy.make("core.List", name="foo2", slug="foo2", type="newsletter")

        payload = {"related_list_slug": "foo2", "override_previous_unsubscribes": "foo"}
        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_1.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "override_previous_unsubscribes": [
                    "'foo' value must be either True or False."
                ]
            },
        )

    def test_subtrig_create_with_bad_related_list_slug(self):
        list_ = mommy.make("core.List", name="foo", slug="foo", type="newsletter")

        payload = {"related_list_slug": "foo2", "override_previous_unsubscribes": "foo"}
        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(), {"related_list_slug": "Related list does not exist."}
        )

    def test_subtrig_create_happy_path(self):
        list_foo = mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="bar", slug="bar", type="newsletter")

        payload = {"related_list_slug": "bar", "override_previous_unsubscribes": False}
        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_foo.pk),
            payload,
            format="json",
        )
        r_json = r.json()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            sorted(r_json.keys()),
            sorted(
                ["id", "override_previous_unsubscribes", "primary_list", "related_list"]
            ),
        )
        self.assertEqual(r_json["override_previous_unsubscribes"], False)
        self.assertEqual(r_json["related_list"]["slug"], list_bar.slug)
        self.assertEqual(r_json["primary_list"]["slug"], list_foo.slug)

    def test_subtrig_get_view(self):
        list_foo = mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="bar", slug="bar", type="newsletter")

        payload = {"related_list_slug": "bar", "override_previous_unsubscribes": True}
        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_foo.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        st_id = r.json()["id"]

        r = self.client.get(
            "/api/lists/{}/subscription-triggers/{}".format(list_foo.pk, st_id)
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r_json = r.json()

        self.assertEqual(
            sorted(r_json.keys()),
            sorted(
                ["id", "override_previous_unsubscribes", "primary_list", "related_list"]
            ),
        )
        self.assertEqual(r_json["override_previous_unsubscribes"], True)
        self.assertEqual(r_json["related_list"]["slug"], list_bar.slug)
        self.assertEqual(r_json["primary_list"]["slug"], list_foo.slug)

    def test_subtrig_get_404(self):
        list_ = mommy.make("core.List", name="foo", slug="foo", type="newsletter")
        r = self.client.get("/api/lists/{}/subscription-triggers/1".format(list_.pk))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(r.json(), {"detail": "Not found."})

    def test_subtrig_update(self):
        mommy.make("core.List", name="bar", slug="bar", type="newsletter")
        list_foo = mommy.make("core.List", name="foo", slug="foo", type="newsletter")

        payload = {"related_list_slug": "bar", "override_previous_unsubscribes": True}
        r = self.client.post(
            "/api/lists/{}/subscription-triggers".format(list_foo.pk),
            payload,
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        st_id = r.json()["id"]

        r = self.client.put(
            "/api/lists/{}/subscription-triggers/{}".format(list_foo.pk, st_id)
        )
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)
