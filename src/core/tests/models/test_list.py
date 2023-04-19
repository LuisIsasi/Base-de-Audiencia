from django.core.exceptions import ValidationError
from django.test import TestCase
from model_mommy import mommy

from ...models import SubscriptionTrigger


class ListTestCase(TestCase):
    def test_str(self):
        slug = "abc-def"
        list_instance = mommy.make(
            "core.List", slug=slug, name="newsletter name", type="newsletter"
        )
        self.assertEqual(str(list_instance), "abc-def")

    def test_slug_with_spaces(self):
        slug = "abc def ghi"
        list_instance = mommy.make(
            "core.List", slug=slug, name="newsletter name", type="newsletter"
        )
        with self.assertRaises(ValidationError) as cm:
            list_instance.full_clean()
        self.assertIn("slug", cm.exception.message_dict.keys())
        self.assertIn(
            "List/newsletter slugs can only contain: lowercase letters, numbers, underscores.",
            cm.exception.message_dict["slug"],
        )

    def test_slug_with_uppercase(self):
        slug = "Abc"
        list_instance = mommy.make(
            "core.List", slug=slug, name="newsletter name", type="newsletter"
        )
        with self.assertRaises(ValidationError) as cm:
            list_instance.full_clean()
        self.assertIn("slug", cm.exception.message_dict.keys())
        self.assertIn(
            "List/newsletter slugs can only contain: lowercase letters, numbers, underscores.",
            cm.exception.message_dict["slug"],
        )

    def test_slug_with_hyphen(self):
        slug = "abc-123-def"
        list_instance = mommy.make(
            "core.List", slug=slug, name="newsletter name", type="newsletter"
        )
        with self.assertRaises(ValidationError) as cm:
            list_instance.full_clean()
        self.assertIn("slug", cm.exception.message_dict.keys())
        self.assertIn(
            "List/newsletter slugs can only contain: lowercase letters, numbers, underscores.",
            cm.exception.message_dict["slug"],
        )

    def test_valid_slug(self):
        slug = "newsletter_name"
        list_instance = mommy.make(
            "core.List", slug=slug, name="newsletter name", type="newsletter"
        )
        list_instance.full_clean()
        self.assertEqual(slug, list_instance.slug)

    def test_slug_empty_str(self):
        list_instance = mommy.make(
            "core.List", name="newsletter name", type="newsletter", slug=""
        )
        with self.assertRaises(ValidationError) as cm:
            list_instance.full_clean()
        self.assertIn("slug", cm.exception.message_dict.keys())
        self.assertIn("This field cannot be blank.", cm.exception.message_dict["slug"])

    def test_slug_missing(self):
        try:
            mommy.make(
                "core.List", name="newsletter name", type="newsletter", slug=None
            )
        except Exception as e:
            # not catching the exception explicitly to avoid coupling to the db backend,
            # and instead doing this weird class name test
            self.assertEqual(e.__class__.__name__, "IntegrityError")
        else:
            self.fail("Expected an exception to be raised.")

    def test_name_missing(self):
        try:
            mommy.make(
                "core.List", slug="newsletter_name", type="newsletter", name=None
            )
        except Exception as e:
            # not catching the exception explicitly to avoid coupling to the db backend,
            # and instead doing this weird class name test
            self.assertEqual(e.__class__.__name__, "IntegrityError")
        else:
            self.fail("Expected an exception to be raised.")

    def test_type_missing(self):
        try:
            mommy.make(
                "core.List", slug="newsletter-name", name="newsletter name", type=None
            )
        except Exception as e:
            # not catching the exception explicitly to avoid coupling to the db backend,
            # and instead doing this weird class name test
            self.assertEqual(e.__class__.__name__, "IntegrityError")
        else:
            self.fail("Expected an exception to be raised.")

    def test_type_invalid(self):
        list_instance = mommy.make(
            "core.List", name="newsletter name", type="foo", slug="fake_slug"
        )
        with self.assertRaises(ValidationError) as cm:
            list_instance.full_clean()
        self.assertIn("type", cm.exception.message_dict.keys())
        self.assertIn(
            "Value 'foo' is not a valid choice.", cm.exception.message_dict["type"]
        )

    def test_sync_externally_default_value(self):
        list_instance = mommy.make(
            "core.List", name="newsletter name", type="foo", slug="fake_slug"
        )
        self.assertEqual(list_instance.sync_externally, True)

    def test_add_and_remove_subscription_triggers(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_foo", name="newsletter foo", type="newsletter"
        )
        list_foo.full_clean()

        list_bar = mommy.make(
            "core.List", slug="newsletter_bar", name="newsletter bar", type="newsletter"
        )
        list_foo.full_clean()

        trigger = list_foo.add_subscription_trigger(list_bar, False)
        self.assertIsInstance(trigger, SubscriptionTrigger)
        self.assertEqual(trigger.primary_list, list_foo)
        self.assertEqual(trigger.related_list, list_bar)
        self.assertEqual(len(list_foo.subscription_triggers.all()), 1)
        self.assertEqual(list_foo.subscription_triggers.all()[0].related_list, list_bar)

        removed_trigger = list_foo.remove_subscription_trigger(list_bar)
        self.assertEqual(list(removed_trigger[1].keys())[0], "core.SubscriptionTrigger")
        self.assertEqual(len(list_foo.subscriptions.all()), 0)

    def test_add_subscription_triggering_itself(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_foo", name="newsletter foo", type="newsletter"
        )
        list_foo.full_clean()

        with self.assertRaises(ValidationError) as cm:
            list_foo.add_subscription_trigger(list_foo, True)
        self.assertEqual(list(cm.exception.message_dict.keys()), ["__all__"])
        self.assertEqual(
            cm.exception.message_dict["__all__"], ["A list cannot trigger itself."]
        )

    def test_add_subscription_trigger_with_override_previous_unsubscribes(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_foo", name="newsletter foo", type="newsletter"
        )
        list_foo.full_clean()

        list_bar = mommy.make(
            "core.List", slug="newsletter_bar", name="newsletter bar", type="newsletter"
        )
        list_foo.full_clean()

        trigger = list_foo.add_subscription_trigger(list_bar, True)
        self.assertIsInstance(trigger, SubscriptionTrigger)
        self.assertEqual(trigger.override_previous_unsubscribes, True)

    def test_add_subscription_trigger_without_override_previous_unsubscribes(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_foo", name="newsletter foo", type="newsletter"
        )
        list_foo.full_clean()

        list_bar = mommy.make(
            "core.List", slug="newsletter_bar", name="newsletter bar", type="newsletter"
        )
        list_foo.full_clean()

        trigger = list_foo.add_subscription_trigger(list_bar, False)
        self.assertIsInstance(trigger, SubscriptionTrigger)
        self.assertEqual(trigger.override_previous_unsubscribes, False)

    def test_add_trigger_to_a_non_list(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_foo", name="newsletter foo", type="newsletter"
        )
        list_foo.full_clean()
        with self.assertRaises(ValueError):
            list_foo.add_subscription_trigger("asdf", False)

    def test_remove_trigger_to_a_non_list(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_foo", name="newsletter foo", type="newsletter"
        )
        list_foo.full_clean()
        with self.assertRaises(SubscriptionTrigger.DoesNotExist):
            list_foo.remove_subscription_trigger(list_foo)

    def test_sailthru_list_name(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_noodles", name="a", type="newsletter"
        )

        self.assertEquals("noodles", list_foo.sailthru_list_name)
        list_foo.slug = "custom_newsletter_noodles"
        self.assertEquals("noodles", list_foo.sailthru_list_name)
        list_foo.slug = "archive_newsletter_noodles"
        self.assertEquals("noodles", list_foo.sailthru_list_name)
        list_foo.slug = "noodles"
        with self.assertRaises(ValueError):
            list_foo.sailthru_list_name

        list_foo.type = "list"
        self.assertEquals("noodles", list_foo.sailthru_list_name)

    def test_sailthru_var_name(self):
        list_foo = mommy.make(
            "core.List", slug="newsletter_noodles", name="a", type="newsletter"
        )

        self.assertEquals("newsletter_noodles", list_foo.sailthru_var_name)
        list_foo.slug = "custom_newsletter_noodles"
        self.assertEquals("custom_newsletter_noodles", list_foo.sailthru_var_name)
        list_foo.slug = "archive_newsletter_noodles"
        self.assertEquals("archive_newsletter_noodles", list_foo.sailthru_var_name)

        list_foo.type = "list"
        list_foo.slug = "noodles"
        self.assertEquals("list_noodles", list_foo.sailthru_var_name)

    def test_clean(self):
        list_foo = mommy.make("core.List", slug="noodles", name="a", type="list")
        invalids = [
            "newsletter_noodles",
            "custom_newsletter_noodles" "archive_newsletter_noodles",
        ]
        for slug in invalids:
            list_foo.slug = slug
            with self.assertRaises(ValidationError):
                list_foo.full_clean()

        list_foo.type = "newsletter"
        list_foo.slug = "noodles"
        with self.assertRaises(ValidationError):
            list_foo.full_clean()
