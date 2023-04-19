import hashlib
import time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from model_mommy import mommy

from ...models import AudienceUser, List, Product, ProductAction, Subscription


class UserTestCase(TestCase):
    def test_str_none(self):
        user = mommy.make("core.AudienceUser", email=None)
        self.assertEqual(str(user), "no email address [pk={}]".format(user.pk))

    def test_str_blank(self):
        user = mommy.make("core.AudienceUser", email="")
        self.assertEqual(str(user), "no email address [pk={}]".format(user.pk))

    def test_str_simple(self):
        user = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertEqual(str(user), user.email)

    def test_str_empty(self):
        user = mommy.make("core.AudienceUser", email="a@a.com")
        user.email = None
        user.pk = None
        self.assertEqual(str(user), "")

    def test_email_field_whitespace_stripping(self):
        au = mommy.make("core.AudienceUser")
        email = "   \t a@a.com\t\t   \r\n"
        au.email = email
        au.save()
        au.refresh_from_db(fields=["email"])
        self.assertEqual(email.strip(), au.email)

    def test_when_email_has_uppercase(self):
        au = mommy.make("core.AudienceUser", email="A@A.com")
        with self.assertRaises(ValidationError) as cm:
            au.validate_and_save()
        self.assertEqual(
            dict(cm.exception.message_dict),
            {"email": ["Email addresses must be lowercase."]},
        )

    def test_email_with_internal_spaces(self):
        au = mommy.make("core.AudienceUser", email="a @a.com")
        with self.assertRaises(ValidationError) as cm:
            au.validate_and_save()
        self.assertEqual(
            dict(cm.exception.message_dict), {"email": ["Enter a valid email address."]}
        )

    def test_when_email_is_none(self):
        au = AudienceUser.objects.validate_and_create(email=None)
        self.assertNotEqual(au.pk, None)

    def test_email_empty_string_becomes_none(self):
        au = AudienceUser.objects.validate_and_create(email="")
        self.assertEqual(au.email, None)

    def test_vars_wrong_type_list(self):
        with self.assertRaises(ValidationError) as cm:
            AudienceUser.objects.validate_and_create(
                email="a@a.com", vars=["this is a list"]
            )
        messages = cm.exception.message_dict
        self.assertIn("vars", messages)
        self.assertIn("This field must be a dictionary.", messages["vars"])

    def test_vars_wrong_type_str(self):
        with self.assertRaises(ValidationError) as cm:
            AudienceUser.objects.validate_and_create(
                email="a@a.com", vars="this is string"
            )
        messages = cm.exception.message_dict
        self.assertIn("vars", messages)
        self.assertIn("This field must be a dictionary.", messages["vars"])

    def test_vars_values_are_not_all_strings(self):
        with self.assertRaises(ValidationError) as cm:
            AudienceUser.objects.validate_and_create(email="a@a.com", vars={"key1": 1})
        self.assertEqual(
            cm.exception.message_dict, {"vars": ["All var values must be strings."]}
        )

    def test_vars_keys_are_not_all_strings(self):
        with self.assertRaises(ValidationError) as cm:
            AudienceUser.objects.validate_and_create(email="a@a.com", vars={1: "val1"})
        messages = cm.exception.message_dict
        self.assertIn("vars", messages)
        self.assertIn("All var keys must be strings.", messages["vars"])

    def test_vars_are_none(self):
        au = AudienceUser.objects.validate_and_create(email="a@a.com", vars=None)
        self.assertEqual(au.vars, {})

    def test_list_subscribe_happy_path(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.list_subscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=True), Subscription
        )

    def test_list_subscribe_to_unknown_list(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertRaises(List.DoesNotExist, au.list_subscribe, "foo")

    def test_list_subscribe_with_comment(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")
        comment = "subscribe comment"
        au.list_subscribe("foo", comment)
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=True), Subscription
        )
        self.assertEqual(au.subscription_log[0].comment, comment)

    def test_list_unsubscribe_happy_path(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.list_subscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=True), Subscription
        )

        au.list_unsubscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=False), Subscription
        )

    def test_list_subscribe_returns_subscription(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertIsInstance(au.list_subscribe("foo"), Subscription)

    def test_list_unsubscribe_returns_subscription(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertIsInstance(au.list_unsubscribe("foo"), Subscription)

    def test_list_unsubscribe_unknown_list(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=True), Subscription
        )
        self.assertRaises(List.DoesNotExist, au.list_unsubscribe, "bar")

    def test_multiple_list_unsubscribe_happy_path(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=True), Subscription
        )

        au.list_unsubscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=False), Subscription
        )

    def test_list_unsubscribe_when_already_unsubscribed(self):
        mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=True), Subscription
        )

        au.list_unsubscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=False), Subscription
        )

        au.list_unsubscribe("foo")
        self.assertEqual(au.subscriptions.all().count(), 1)
        self.assertIsInstance(
            au.subscriptions.get(list__slug="foo", active=False), Subscription
        )

    def test__list_sub_or_unsub_with_unknown_action(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertRaises(ValueError, au._list_sub_or_unsub, "list_slug", "foo")

    def test_record_product_action_registered(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        action = au.record_product_action("foo", "registered", timezone.now())
        self.assertIsInstance(action, ProductAction)

    def test_record_product_action_consumed(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        action = au.record_product_action("foo", "consumed", timezone.now())
        self.assertIsInstance(action, ProductAction)

    def test_record_product_action_bogus_action_type(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        with self.assertRaises(ValidationError) as cm:
            au.record_product_action("foo", "bar", timezone.now())
        self.assertEqual(list(cm.exception.message_dict.keys()), ["type"])
        self.assertEqual(
            cm.exception.message_dict["type"], ["Value 'bar' is not a valid choice."]
        )

    def test_record_product_action_bogus_product_slug(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        self.assertRaises(
            Product.DoesNotExist,
            au.record_product_action,
            "foo",
            "consumed",
            timezone.now(),
        )

    def test_record_product_action_with_details(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        action = au.record_product_action(
            "foo", "consumed", timezone.now(), details=["test details"]
        )
        self.assertIsInstance(action, ProductAction)
        self.assertEquals(action.details.all().count(), 1)
        self.assertEquals(action.details.all()[0].description, "test details")

    def test_record_product_action_with_multiple_details(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        action = au.record_product_action(
            "foo", "consumed", timezone.now(), details=["foo", "bar"]
        )
        self.assertIsInstance(action, ProductAction)
        self.assertEquals(action.details.all().count(), 2)
        self.assertEquals(action.details.all()[0].description, "bar")
        self.assertEquals(action.details.all()[1].description, "foo")

    def test_record_product_action_with_details_as_str(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )
        self.assertRaises(
            TypeError,
            au.record_product_action,
            "foo",
            "consumed",
            timezone.now(),
            "test details",
        )

    def test_update_product_action(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )

        original_timestamp = timezone.now()
        action = au.record_product_action("foo", "registered", original_timestamp)
        original_modified = action.modified
        self.assertIsInstance(action, ProductAction)

        time.sleep(0.1)

        action_updated = au.record_product_action("foo", "registered", timezone.now())
        self.assertNotEqual(id(action), id(action_updated))
        self.assertEqual(action_updated.pk, action.pk)
        self.assertEqual(action_updated.product, action.product)
        self.assertEqual(action_updated.audience_user, action.audience_user)
        self.assertEqual(action_updated.type, action.type)
        self.assertEqual(action_updated.timestamp, original_timestamp)
        self.assertNotEqual(action_updated.modified, original_modified)

    def test_append_product_action_details(self):
        au = mommy.make("core.AudienceUser", email="a@a.com")
        product_subtype = mommy.make("core.ProductSubtype", name="subtype1")
        product_topic = mommy.make("core.ProductTopic", name="topic1")
        mommy.make(
            "core.Product",
            slug="foo",
            name="Foo",
            brand="Govexec",
            type="event",
            subtypes=[product_subtype],
            topics=[product_topic],
        )

        first_timestamp = timezone.now()
        action = au.record_product_action(
            "foo", "registered", first_timestamp, details=["first detail"]
        )
        self.assertIsInstance(action, ProductAction)
        self.assertEqual(action.details.all().count(), 1)
        self.assertEqual(action.details.all()[0].description, "first detail")
        self.assertEqual(action.details.all()[0].timestamp, first_timestamp)

        time.sleep(0.1)

        second_timestamp = timezone.now()
        updated_action = au.record_product_action(
            "foo", "registered", second_timestamp, details=["second detail"]
        )
        self.assertIsInstance(updated_action, ProductAction)

        self.assertEqual(action.details.all().count(), 2)
        self.assertEqual(action.details.all()[0].description, "second detail")
        self.assertEqual(action.details.all()[1].description, "first detail")
        self.assertEqual(action.details.all()[0].timestamp, second_timestamp)
        self.assertEqual(action.details.all()[1].timestamp, first_timestamp)

    def test_email_hash(self):
        email_address = "foo@bar.com"
        au = AudienceUser.objects.validate_and_create(email=email_address)
        hasher = hashlib.md5()
        hasher.update(email_address.encode("utf-8"))
        self.assertEqual(hasher.hexdigest(), au.email_hash)

    def test_email_hash_no_email(self):
        email_address = None
        au = AudienceUser.objects.validate_and_create(email=email_address)
        self.assertEqual(au.email_hash, None)
