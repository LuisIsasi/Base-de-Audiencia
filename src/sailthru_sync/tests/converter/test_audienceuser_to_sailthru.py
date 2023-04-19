import pytz
import random
import string
from datetime import datetime, timedelta
from itertools import chain

from django import test
from django.utils.timezone import localtime
from model_mommy import mommy

import sailthru_sync.converter.audienceuser_to_sailthru as converter
from core import models as core_models


@test.override_settings(SAILTHRU_SYNC_SIGNALS_ENABLED=False, RAVEN_CONFIG={"dsn": None})
class AudienceUserToSailthruTest(test.TestCase):
    def _random_string(self):
        return "".join(
            random.choice(string.ascii_letters) for x in range(random.randint(1, 20))
        )

    def test_email_required(self):
        user = mommy.make("core.AudienceUser", email=None)
        to_sailthru = converter.AudienceUserToSailthru(user)
        with self.assertRaises(converter.ConversionError):
            to_sailthru.convert()

    def test_varkey_sync_with_sailthru(self):
        mommy.make(
            "core.VarKey",
            key="sync",
            sync_with_sailthru=True,
        )
        mommy.make(
            "core.VarKey",
            key="dont_sync",
            sync_with_sailthru=False,
        )
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
            vars={
                "sync": None,
                "dont_sync": None,
            },
        )

        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertTrue(len(to_sailthru.vars_to_sync) == 1)
        self.assertTrue(to_sailthru.vars_to_sync[0] == "sync")

    def test_one_to_one(self):
        """
        Tests to make sure that the values returned in the `one_to_one` method
        are only the ones that are in the one_to_one field list
        """

        varkeys = [
            "agency_department",
            "birth_date",
            "country",
            "education_level",
            "email",
            "employer",
            "first_name",
            "gender",
            "grade_rank",
            "income",
            "industry",
            "job_function",
            "job_title",
            "last_name",
            "locale",
            "marital",
            "phone",
            "postal_address",
            "postal_address2",
            "postal_city",
            "postal_code",
            "postal_state",
            "procurement_level",
            "timezone",
            "procurement_subject",
        ]
        for var in varkeys:
            mommy.make("core.VarKey", key=var, sync_with_sailthru=True)

        user_vars = dict((var, var) for var in varkeys)

        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars=user_vars)
        to_sailthru = converter.AudienceUserToSailthru(user)
        one_to_one = to_sailthru.get_one_to_one_fields()
        keys = one_to_one.keys()
        values = one_to_one.values()
        self.assertNotIn("procurement_subject", keys)

        correct_keys = set(varkeys) - {
            "procurement_subject",
            "app_interest_route_fifty",
        }
        self.assertTrue(correct_keys == set(keys))
        self.assertSequenceEqual(sorted(keys), sorted(values))

    def test_get_name_w_data(self):
        """
        Tests that get_name will construct a full name from its parts
        """
        first_name = "first"
        last_name = "last"

        mommy.make("core.VarKey", key="first_name", sync_with_sailthru=True)
        mommy.make("core.VarKey", key="last_name", sync_with_sailthru=True)

        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})

        user.vars["first_name"] = first_name
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertIn(first_name, to_sailthru.get_name())

        user.vars = {}
        user.vars["last_name"] = last_name
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertIn(last_name, to_sailthru.get_name())

        user.vars = {}
        user.vars["first_name"] = first_name
        user.vars["last_name"] = last_name
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertIn(last_name, to_sailthru.get_name())

    def test_get_source_empty(self):
        """
        Tests that get_source will be unsyncable with there are no source signups
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})

        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(None, to_sailthru.get_source())

    def test_get_source_signup_date_empty(self):
        """
        Tests that get_source_signup_date will be unsyncable with there are no source signups
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})

        to_sailthru = converter.AudienceUserToSailthru(user)
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(None, to_sailthru.get_source_signup_date())

    def test_get_sources_empty(self):
        """
        Tests that get_sources will return an iterable of length 0
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})

        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(to_sailthru.get_sources(), 0)

    def test_get_source_first(self):
        """
        Tests that get_source will return the earliest signup
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})
        newest_signup = mommy.make(
            "core.UserSource",
            audience_user=user,
            name="newest",
        )
        oldest_signup = mommy.make(
            "core.UserSource",
            audience_user=user,
            name="oldest",
        )
        oldest = newest_signup.timestamp - timedelta(days=100)
        core_models.UserSource.objects.filter(name="oldest").update(timestamp=oldest)
        oldest_signup.refresh_from_db()

        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(oldest_signup.name, to_sailthru.get_source())

    def test_get_source_signup_date_first(self):
        """
        Tests that get_source_signup_date will return the earliest signup
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})
        newest_signup = mommy.make(
            "core.UserSource",
            audience_user=user,
            name="newest",
        )
        oldest_signup = mommy.make(
            "core.UserSource",
            audience_user=user,
            name="oldest",
        )
        oldest = newest_signup.timestamp - timedelta(days=100)
        core_models.UserSource.objects.filter(name="oldest").update(timestamp=oldest)
        oldest_signup.refresh_from_db()

        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(
            localtime(oldest_signup.timestamp).strftime(
                to_sailthru.source_signup_date_format
            ),
            to_sailthru.get_source_signup_date(),
        )

    def test_get_sources(self):
        """
        Tests that get_source will return all the signups
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})
        signup_a = mommy.make(
            "core.UserSource",
            audience_user=user,
            name="a",
        )
        signup_b = mommy.make(
            "core.UserSource",
            audience_user=user,
            name="b",
        )

        to_sailthru = converter.AudienceUserToSailthru(user)
        sources = to_sailthru.get_sources()
        self.assertEqual(len(sources), 2)
        self.assertIn(signup_a.name, sources)
        self.assertIn(signup_b.name, sources)

    def test_get_email_domain(self):
        """
        Tests that get_email_domain can handle a few different type of values
        """
        user = mommy.make("core.AudienceUser", email="aa@aa.com", vars={})
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(to_sailthru.get_email_domain(), "aa.com")

        emails = ["", "asdf"]
        for email in emails:
            user.email = email
            to_sailthru = converter.AudienceUserToSailthru(user)
            with self.assertRaises(IndexError):
                to_sailthru.get_email_domain()
        user.email = "@"
        to_sailthru = converter.AudienceUserToSailthru(user)
        with self.assertRaises(Exception):
            to_sailthru.get_email_domain()

    def test_get_procurement_subject(self):
        """
        Tests that get_procurement_subject can handle different values
        """
        mommy.make("core.VarKey", key="procurement_subject", sync_with_sailthru=True)
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        tests = [
            ("", ""),
            ("abc", "abc"),
            ("abc::def::ghi", "abc,def,ghi"),
            ("abc::def::gh,i", "abc,def,gh,i"),
            ("a,b,c", "a,b,c"),
        ]
        for test_value, expected_conversion in tests:
            user.vars["procurement_subject"] = test_value
            to_sailthru = converter.AudienceUserToSailthru(user)
            self.assertEqual(expected_conversion, to_sailthru.get_procurement_subject())
        user.vars["procurement_subject"] = None
        to_sailthru = converter.AudienceUserToSailthru(user)
        with self.assertRaises(Exception):
            to_sailthru.get_procurement_subject()

    def test_get_modified_time(self):
        """
        Tests that get_modified_time returns the user's modified timestamp
        """
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertEqual(
            int(user.modified.timestamp()), to_sailthru.get_modified_time()
        )
        self.assertTrue(isinstance(to_sailthru.get_modified_time(), int))

    def test_get_sync_time(self):
        """
        Tests that get_modified_time returns the user's modified timestamp
        """
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertTrue(isinstance(to_sailthru.get_sync_time(), int))

    def test_get_var_subscriptions(self):
        """
        Tests that get_var_subscriptions retrieves proper items
        """
        self._test_get_var_list_subscriptions("newsletter")

    def test_get_list_subscriptions(self):
        """
        Tests that get_list_subscriptions retrieves proper items
        """
        self._test_get_var_list_subscriptions("list")

    def _test_get_var_list_subscriptions(self, list_type):
        actives = []
        inactives = []
        for x in range(3):
            active = mommy.make(
                "core.List",
                name="{}_{}".format(list_type, x),
                slug="{}_{}".format(list_type, x),
                type=list_type,
            )
            actives.append(active.slug)

            inactive = mommy.make(
                "core.List",
                name="{}_i-sync-externally-{}".format(list_type, x),
                slug="{}_i-sync-externally-{}".format(list_type, x),
                type=list_type,
                sync_externally=False,
            )
            inactives.append(inactive.slug)
            inactive = mommy.make(
                "core.List",
                name="{}_i-archived-{}".format(list_type, x),
                slug="{}_i-archived-{}".format(list_type, x),
                type=list_type,
            )

        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )

        for list_ in chain(actives, inactives):
            user.list_subscribe(list_)

        core_models.List.objects.filter(slug__contains="i-archived").update(
            archived=True
        )

        if list_type == "newsletter":
            func_name = "get_var_subscriptions"
        else:
            func_name = "get_list_subscriptions"
        to_sailthru = converter.AudienceUserToSailthru(user)
        for slug, _ in getattr(to_sailthru, func_name)().items():
            self.assertIn(slug, actives)
            self.assertNotIn(slug, inactives)

        for list_ in actives:
            user.list_unsubscribe(list_)
        to_sailthru = converter.AudienceUserToSailthru(user)
        for _, active in getattr(to_sailthru, func_name)().items():
            self.assertFalse(active)

    def test_get_var_list_subscriptions_empty(self):
        """
        Tests that get_list_subscriptions will return empty dict when no subscriptions
        """
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )

        to_sailthru = converter.AudienceUserToSailthru(user)
        self.assertFalse(bool(to_sailthru.get_list_subscriptions()))
        self.assertFalse(bool(to_sailthru.get_var_subscriptions()))

    def test__get_aggregated_topic_product_vars(self):
        topic = mommy.make("core.ProductTopic", _fill_optional=True)
        product = mommy.make(
            "core.Product", name="a", slug="a", _fill_optional=["brand", "type"]
        )
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        user.record_product_action(
            product.slug, "registered", pytz.utc.localize(datetime.now())
        )
        user.record_product_action(
            product.slug, "consumed", pytz.utc.localize(datetime.now())
        )
        product_actions = user.product_actions.all()

        to_sailthru = converter.AudienceUserToSailthru(user)
        topic_vars = to_sailthru._get_aggregated_topic_product_vars(product_actions)
        self.assertEqual(topic_vars["product_topics"], 0)

        product.topics.add(topic)

        product_actions = user.product_actions.all()
        topic_vars = to_sailthru._get_aggregated_topic_product_vars(product_actions)
        topics = topic_vars["product_topics"]
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0], topic.name)

    def test__get_aggregated_action_product_vars(self):
        products = []
        for type_, _ in core_models.Product.PRODUCT_TYPE_CHOICES:
            product = mommy.make(
                "core.Product",
                name=type_,
                slug=type_,
                type=type_,
                _fill_optional=["brand"],
            )
            products.append(product)
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        product_actions = user.product_actions.all()

        to_sailthru = converter.AudienceUserToSailthru(user)
        data = to_sailthru._get_aggregated_action_product_vars(
            [x for x in product_actions if x.type == "registered"],
            [x for x in product_actions if x.type == "consumed"],
        )
        self.assertEqual(len(data), len(core_models.Product.PRODUCT_TYPE_CHOICES) * 2)
        for key, value in data.items():
            self.assertEqual(value, 0)

        for product in products:
            user.record_product_action(
                product.slug, "registered", pytz.utc.localize(datetime.now())
            )
            user.record_product_action(
                product.slug, "consumed", pytz.utc.localize(datetime.now())
            )

        product_actions = user.product_actions.all()
        data = to_sailthru._get_aggregated_action_product_vars(
            [x for x in product_actions if x.type == "registered"],
            [x for x in product_actions if x.type == "consumed"],
        )
        for product in products:
            consumed_var = "{}s_{}".format(product.type, product.consumed_verb)
            registered_var = "{}s_{}".format(product.type, product.registered_verb)
            self.assertIn(consumed_var, data)
            self.assertIn(registered_var, data)

            for key, value in data.items():
                if key in [registered_var, consumed_var]:
                    self.assertEqual(len(value), 1)
                    self.assertEqual(value[0], product.slug)

    def test__get_action_product_vars(self):
        products = []
        for type_, _ in core_models.Product.PRODUCT_TYPE_CHOICES:
            product = mommy.make(
                "core.Product",
                name=type_,
                slug=type_,
                type=type_,
                _fill_optional=["brand"],
            )
            products.append(product)
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        product_actions = user.product_actions.all()

        to_sailthru = converter.AudienceUserToSailthru(user)
        data = to_sailthru._get_action_product_vars(
            [x for x in product_actions if x.type == "registered"],
            [x for x in product_actions if x.type == "consumed"],
        )
        self.assertEqual(len(data), 0)

        alt = 0
        for product in products:
            registered_args = [
                product.slug,
                "registered",
                pytz.utc.localize(datetime.now()),
            ]
            consumed_args = [
                product.slug,
                "consumed",
                pytz.utc.localize(datetime.now()),
            ]
            if alt % 2:
                alt = 0
            else:
                alt = 1
                registered_args.append(
                    [self._random_string() for x in range(random.randint(1, 5))]
                )
                consumed_args.append(
                    [self._random_string() for x in range(random.randint(1, 5))]
                )

            user.record_product_action(*registered_args)
            user.record_product_action(*consumed_args)

        product_actions = user.product_actions.all()

        to_sailthru = converter.AudienceUserToSailthru(user)
        data = to_sailthru._get_action_product_vars(
            [x for x in product_actions if x.type == "registered"],
            [x for x in product_actions if x.type == "consumed"],
        )

        num_types = len(core_models.Product.PRODUCT_TYPE_CHOICES)
        num_actions = 2
        num_vars_per_action = 2
        self.assertEqual(len(data), num_types * num_actions * num_vars_per_action)
        for action in product_actions:
            if action.type == "registered":
                self.assertIn(action.sailthru_registered_var, data)
                self.assertEqual(
                    int(action.sailthru_registered_value),
                    data[action.sailthru_registered_var],
                )
            else:
                self.assertIn(action.sailthru_consumed_var, data)
                self.assertEqual(
                    int(action.sailthru_consumed_value),
                    data[action.sailthru_consumed_var],
                )

    def test_get_product_vars(self):
        """Can I be a little wimpy with this test since I've done all the pieces?"""
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        product = mommy.make(
            "core.Product", name="a", slug="a", _fill_optional=["brand", "type"]
        )
        topic = mommy.make("core.ProductTopic", _fill_optional=True)
        product.topics.add(topic)
        user.record_product_action(
            product.slug, "registered", pytz.utc.localize(datetime.now())
        )
        user.record_product_action(
            product.slug, "consumed", pytz.utc.localize(datetime.now())
        )
        to_sailthru = converter.AudienceUserToSailthru(user)
        data = to_sailthru.get_product_vars()
        self.assertIn("product_topics", data)
        for type_, _ in core_models.Product.PRODUCT_TYPE_CHOICES:
            consumed_verb = core_models.Product.consumed_verb_for_type(type_)
            registered_verb = core_models.Product.registered_verb_for_type(type_)
            registered_key = "{}s_{}".format(type_, registered_verb)
            consumed_key = "{}s_{}".format(type_, consumed_verb)
            self.assertIn(registered_key, data)
            self.assertIn(consumed_key, data)
            if type_ == product.type:
                self.assertIn(product.slug, data[registered_key])
                self.assertIn(product.slug, data[consumed_key])
        for action in user.product_actions.all():
            if action.type == "registered":
                self.assertIn(action.sailthru_registered_var, data)
                self.assertIn(action.sailthru_registered_details_var, data)
            else:
                self.assertIn(action.sailthru_consumed_var, data)
                self.assertIn(action.sailthru_consumed_details_var, data)

    def test_get_fields(self):
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        to_sailthru = converter.AudienceUserToSailthru(user)
        data = to_sailthru.get_fields()
        required_fields = ["keys"]
        for field in required_fields:
            self.assertIn(field, data)
            self.assertEqual(data[field], 1)

    def test_to_string(self):
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
        )
        to_sailthru = converter.AudienceUserToSailthru(user)
        str(to_sailthru)

    def test_convert(self):
        """Can I be a little wimpy with this test since I've done all the pieces?"""
        user = mommy.make(
            "core.AudienceUser",
            email="aa@aa.com",
            vars={"first_name": "a", "last_name": "b", "procurement_subject": "abc"},
        )
        mommy.make(
            "core.UserSource",
            audience_user=user,
            name="signup",
        )
        to_sailthru = converter.AudienceUserToSailthru(user)
        data = to_sailthru.convert()
        keys = [
            "id",
            "key",
            "lists",
            "vars",
            "fields",
        ]
        for key in keys:
            self.assertIn(key, data)

        var_keys = [
            "email_domain",
            "audb_last_modified_time",
            "last_synced_time",
            "sources",
        ]
        for key in var_keys:
            self.assertIn(key, data["vars"])
