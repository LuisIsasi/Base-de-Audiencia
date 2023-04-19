from datetime import datetime


import isodate
from django.utils.timezone import localtime, now
from model_mommy import mommy
from rest_framework import status
from rest_framework import test as rest_test

from ...models import AudienceUser


class UserViewsetTests(rest_test.APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token

        u = User.objects.create(username="test")
        t = Token.objects.create(user=u)
        self.client.force_authenticate(user=u, token=t)

    def test_create_user_with_email(self):
        email = "a@a.com"
        response = self.client.post(
            "/api/audience-users", {"email": email}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = AudienceUser.objects.get(email=email)
        response = self.client.get("/api/audience-users/{}".format(user.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_without_email(self):
        response = self.client.post("/api/audience-users", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_json = response.json()
        user = AudienceUser.objects.get(pk=response_json["id"])
        self.assertEqual(user.email, None)

        response = self.client.get("/api/audience-users/{}".format(user.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_users_none(self):
        r = self.client.get("/api/audience-users")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 0)

    def test_list_users(self):
        mommy.make("core.AudienceUser", email="a@a.com")
        r = self.client.get("/api/audience-users")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 1)

    def test_list_users_filter(self):
        mommy.make("core.AudienceUser", email="a@a.com")
        r = self.client.get("/api/audience-users?email=a@a.com")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json().get("count"), 1)

    def test_create_user_update_non_var_field(self):
        omeda_id = "1234"
        payload = {"email": "a@a.com", "omeda_id": omeda_id}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.json()["omeda_id"], omeda_id)

        new_omeda_id = "5678"
        put_payload = {"omeda_id": new_omeda_id}
        r = self.client.put(
            "/api/audience-users/{}".format(r.json()["id"]), put_payload, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["omeda_id"], new_omeda_id)

    def test_create_user_with_vars(self):
        payload = {"email": "a@a.com", "vars": {"a": "b"}}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.get("/api/audience-users/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["vars"], payload["vars"])

    def test_create_user_with_reserved_var(self):
        res_vars = {
            "newsletter_foo": "newsletter_foo is invalid because it matches a reserved prefix: newsletter_.",
            "events_attended": "events_attended is invalid because it matches a reserved prefix: events_.",
            "name": "name is invalid because it matches a reserved word.",
            "source": "source is invalid because it matches a reserved word.",
            "product_topics": "product_topics is invalid because it matches a reserved word.",
            "list_bar": "list_bar is invalid because it matches a reserved prefix: list_.",
        }
        for res_var, res_var_error_msg in res_vars.items():
            payload = {"email": "a@a.com", "vars": {res_var: "1"}}
            r = self.client.post("/api/audience-users", payload, format="json")
            self.assertEqual(r.json(), {"vars": [res_var_error_msg]})
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_update_existing_var(self):
        payload = {"email": "a@a.com", "vars": {"a": "b"}}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.get("/api/audience-users/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["vars"], payload["vars"])

        put_payload = {"vars": {"a": "c"}}
        r = self.client.put(
            "/api/audience-users/{}".format(r.json()["id"]), put_payload, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        r = self.client.get("/api/audience-users/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["vars"], put_payload["vars"])

    def test_create_user_add_var(self):
        payload = {"email": "a@a.com", "vars": {"a": "b"}}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.get("/api/audience-users/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["vars"], payload["vars"])

        put_payload = {"vars": {"c": "d"}}
        r = self.client.put(
            "/api/audience-users/{}".format(r.json()["id"]), put_payload, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        payload["vars"].update(put_payload["vars"])
        r = self.client.get("/api/audience-users/{}".format(r.json()["id"]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["vars"], payload["vars"])

    def test_user_contains_expected_keys(self):
        payload = {"email": "a@a.com", "vars": {"a": "b"}}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        user = r.json()
        expected_keys = [
            "id",
            "email",
            "created",
            "modified",
            "email_hash",
            "omeda_id",
            "sailthru_id",
            "vars",
            "vars_history",
            "source_signups",
            "subscriptions",
            "subscription_log",
            "product_actions",
            "sailthru_optout",
        ]
        self.assertCountEqual(user.keys(), expected_keys)

    def test_user_malformed_source_signups_as_string(self):
        payload = {"email": "a@a.com", "source_signups": "asdf"}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(
            r.json(),
            {
                "source_signups": {
                    "non_field_errors": ['Expected a list of items but got type "str".']
                }
            },
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_empty_source_signups_list(self):
        payload = {"email": "a@a.com", "source_signups": []}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.json()["source_signups"], [])

    def test_user_source_signup_without_name(self):
        payload = {"email": "a@a.com", "source_signups": [{}]}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(), {"source_signups": [{"name": ["This field is required."]}]}
        )

    def test_user_source_signup_without_timestamp(self):
        payload = {"email": "a@a.com", "source_signups": [{"name": "foo_source"}]}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        user = r.json()
        self.assertEqual(len(user["source_signups"]), 1)
        self.assertEqual(user["source_signups"][0]["name"], "foo_source")
        self.assertCountEqual(
            user["source_signups"][0].keys(),
            [
                "timestamp",
                "name",
            ],
        )
        self.assertIsInstance(
            isodate.parse_datetime(user["source_signups"][0]["timestamp"]), datetime
        )

    def test_user_source_signup_with_bad_timestamp(self):
        payload = {
            "email": "a@a.com",
            "source_signups": [{"name": "foo_source", "timestamp": "foo"}],
        }
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.json(),
            {
                "source_signups": [
                    {
                        "timestamp": [
                            "Datetime has wrong format. Use one of these formats instead: "
                            "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                        ]
                    }
                ]
            },
        )

    def test_user_source_signup_with_timestamp(self):
        timestamp = localtime(now()).isoformat()
        payload = {
            "email": "a@a.com",
            "source_signups": [{"name": "foo_source", "timestamp": timestamp}],
        }
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        user = r.json()
        self.assertEqual(len(user["source_signups"]), 1)
        self.assertEqual(user["source_signups"][0]["name"], "foo_source")
        self.assertCountEqual(
            user["source_signups"][0].keys(),
            [
                "timestamp",
                "name",
            ],
        )
        self.assertIsInstance(
            isodate.parse_datetime(user["source_signups"][0]["timestamp"]), datetime
        )
        self.assertEqual(
            localtime(isodate.parse_datetime(user["source_signups"][0]["timestamp"])),
            localtime(isodate.parse_datetime(timestamp)),
        )

    def test_user_source_signup_multiple_additions(self):
        # adding this test because we had a bug where the latest source_signups
        # were not being returned in the representation provided with the response
        # to the PUT/update request, and we want to make sure to avoid a regression here
        payload = {"email": "a@a.com", "source_signups": [{"name": "foo_source"}]}
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        user = r.json()

        put_payload = {"source_signups": [{"name": "bar_source"}]}
        r = self.client.put(
            "/api/audience-users/{}".format(user["id"]), put_payload, format="json"
        )
        user = r.json()
        self.assertEqual(
            [x["name"] for x in user["source_signups"]], ["bar_source", "foo_source"]
        )

        put_payload = {"source_signups": [{"name": "baz_source"}]}
        r = self.client.put(
            "/api/audience-users/{}".format(user["id"]), put_payload, format="json"
        )
        user = r.json()
        self.assertEqual(
            [x["name"] for x in user["source_signups"]],
            ["baz_source", "bar_source", "foo_source"],
        )

    def test_user_source_signup_multiple_additions_with_timestamps(self):
        payload = {
            "email": "a@a.com",
            "source_signups": [
                {"name": "foo_source", "timestamp": "2016-03-29T21:15:30.249694Z"}
            ],
        }
        r = self.client.post("/api/audience-users", payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        user = r.json()

        put_payload = {
            "source_signups": [
                {"name": "bar_source", "timestamp": "2015-01-28T20:10:13.249694Z"}
            ]
        }
        r = self.client.put(
            "/api/audience-users/{}".format(user["id"]), put_payload, format="json"
        )
        user = r.json()
        self.assertEqual(
            [x["name"] for x in user["source_signups"]], ["foo_source", "bar_source"]
        )

    def test_user_delete(self):
        user = mommy.make("core.AudienceUser", email="a@a.com")
        r = self.client.delete("/api/audience-users/{}".format(user.pk), format="json")
        self.assertEqual(r.status_code, status.HTTP_501_NOT_IMPLEMENTED)
