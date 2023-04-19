from django import test
from model_mommy import mommy

from ..models import SubscriptionTrigger


class TriggeredListSubscribesTestCases(test.TestCase):
    def test_triggered_subscribe(self):
        list_foo = mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="Bar", slug="bar", type="newsletter")

        sub_trigger = list_foo.add_subscription_trigger(
            list_bar, override_previous_unsubscribes=False
        )
        self.assertIsInstance(sub_trigger, SubscriptionTrigger)

        au = mommy.make("core.AudienceUser", email="a@a.com")
        au.list_subscribe("foo")

        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["bar", "foo"],
        )

    def test_triggered_subscribe_when_already_subscribed(self):
        list_foo = mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="Bar", slug="bar", type="newsletter")
        list_baz = mommy.make("core.List", name="Baz", slug="baz", type="newsletter")

        sub_trigger = list_bar.add_subscription_trigger(
            list_baz, override_previous_unsubscribes=False
        )
        self.assertIsInstance(sub_trigger, SubscriptionTrigger)

        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("foo")
        au.list_subscribe("baz")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["baz", "foo"],
        )

        au.list_subscribe("bar")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["bar", "baz", "foo"],
        )

    def test_triggered_subscribe_does_not_override_prev_unsub(self):
        list_foo = mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="Bar", slug="bar", type="newsletter")

        sub_trigger = list_foo.add_subscription_trigger(
            list_bar, override_previous_unsubscribes=False
        )
        self.assertIsInstance(sub_trigger, SubscriptionTrigger)

        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("bar")
        au.list_subscribe("foo")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["bar", "foo"],
        )

        au.list_unsubscribe("foo")
        au.list_unsubscribe("bar")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]), []
        )
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if not x.active]),
            ["bar", "foo"],
        )

        au.list_subscribe("foo")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]), ["foo"]
        )
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if not x.active]),
            ["bar"],
        )

    def test_triggered_subscribe_overrides_prev_unsub(self):
        list_foo = mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="Bar", slug="bar", type="newsletter")

        sub_trigger = list_foo.add_subscription_trigger(
            list_bar, override_previous_unsubscribes=True
        )
        self.assertIsInstance(sub_trigger, SubscriptionTrigger)

        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("bar")
        au.list_subscribe("foo")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["bar", "foo"],
        )

        au.list_unsubscribe("foo")
        au.list_unsubscribe("bar")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]), []
        )
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if not x.active]),
            ["bar", "foo"],
        )

        au.list_subscribe("foo")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["bar", "foo"],
        )
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if not x.active]), []
        )

    def test_triggered_subscribes_do_not_cascade(self):
        list_foo = mommy.make("core.List", name="Foo", slug="foo", type="newsletter")
        list_bar = mommy.make("core.List", name="Bar", slug="bar", type="newsletter")
        list_baz = mommy.make("core.List", name="Baz", slug="baz", type="newsletter")

        sub_trigger_bar = list_foo.add_subscription_trigger(
            list_bar, override_previous_unsubscribes=True
        )
        self.assertIsInstance(sub_trigger_bar, SubscriptionTrigger)

        sub_trigger_baz = list_bar.add_subscription_trigger(
            list_baz, override_previous_unsubscribes=True
        )
        self.assertIsInstance(sub_trigger_baz, SubscriptionTrigger)

        au = mommy.make("core.AudienceUser", email="a@a.com")

        au.list_subscribe("foo")
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if x.active]),
            ["bar", "foo"],
        )
        self.assertEqual(
            sorted([x.list.slug for x in au.subscriptions.all() if not x.active]), []
        )
