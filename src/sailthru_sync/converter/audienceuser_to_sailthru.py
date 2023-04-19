from datetime import datetime

import core.models as core_models
from django.utils.timezone import localtime
from nameparser import HumanName

from .errors import ConversionError


class AudienceUserToSailthru(object):
    source_signup_date_format = "%Y-%m-%d %H:%M"

    complex_fields = [
        "procurement_subject",
    ]

    def __init__(self, user):
        self.user = user
        self.vars_to_sync = core_models.VarKey.objects.filter(
            key__in=self.user.vars.keys(), sync_with_sailthru=True
        ).values_list("key", flat=True)

    def __str__(self):
        return "<{} converter for audience user: {}>".format(
            self.__class__.__name__, self.user
        )

    def get_one_to_one_fields(self):
        data = {}
        for field in self.vars_to_sync:
            if field not in self.complex_fields:
                data[field] = self.user.vars[field]
        return data

    def get_name(self):
        name = HumanName()
        if "first_name" in self.vars_to_sync:
            name.first = self.user.vars["first_name"]
        if "last_name" in self.vars_to_sync:
            name.last = self.user.vars["last_name"]
        return str(name)

    def get_source(self):
        signups = list(self.user.source_signups.all())
        if signups:
            return signups[-1].name
        return None

    def get_source_signup_date(self):
        signups = list(self.user.source_signups.all())
        if signups:
            last_signup_time = localtime(signups[-1].timestamp)
            return last_signup_time.strftime(self.source_signup_date_format)
        return None

    def get_sources(self):
        signups = {signup.name for signup in self.user.source_signups.all()}
        return sorted(list(signups)) or 0

    def get_email_domain(self):
        domain = self.user.email.split("@")[1]
        if not domain:
            raise ConversionError("Invalid email domain.")
        return domain

    def get_procurement_subject(self):
        subject = self.user.vars.get("procurement_subject", "")
        return ",".join(subject.split("::"))

    def get_modified_time(self):
        return int(self.user.modified.timestamp())

    def get_sync_time(self):
        return int(datetime.now().timestamp())

    def get_var_subscriptions(self):
        return dict(
            (s.list.sailthru_var_name, 1 if s.active else 0)
            for s in self.user.subscriptions.all()
            if s.list.can_sync()
        )

    def get_list_subscriptions(self):
        return dict(
            (s.list.sailthru_list_name, 1 if s.active else 0)
            for s in self.user.subscriptions.all()
            if s.list.can_sync()
        )

    def _get_aggregated_topic_product_vars(self, product_actions):
        topics = set()
        for action in product_actions:
            for topic in action.product.topics.all():
                topics.add(topic.name)
        data = {
            "product_topics": sorted(list(topics)) or 0,
        }
        return data

    def _get_aggregated_action_product_vars(self, registered_actions, consumed_actions):
        data = {}
        product_var = "{}s_{}"
        for product_type in core_models.Product.product_types():
            consumed_verb = core_models.Product.consumed_verb_for_type(product_type)
            registered_verb = core_models.Product.registered_verb_for_type(product_type)

            consumed_product_var = product_var.format(product_type, consumed_verb)
            registered_product_var = product_var.format(product_type, registered_verb)

            data[consumed_product_var] = (
                sorted(
                    [
                        action.product.slug
                        for action in consumed_actions
                        if action.product.type == product_type
                    ]
                )
                or 0
            )

            data[registered_product_var] = (
                sorted(
                    [
                        action.product.slug
                        for action in registered_actions
                        if action.product.type == product_type
                    ]
                )
                or 0
            )

        return data

    def _get_action_product_vars(self, registered_actions, consumed_actions):
        data = {}
        for action in registered_actions:
            time_var = action.sailthru_registered_var
            details_var = action.sailthru_registered_details_var

            data[time_var] = int(action.sailthru_registered_value)
            data[details_var] = action.sailthru_registered_details_value

        for action in consumed_actions:
            time_var = action.sailthru_consumed_var
            details_var = action.sailthru_consumed_details_var

            data[time_var] = int(action.sailthru_consumed_value)
            data[details_var] = action.sailthru_consumed_details_value

        return data

    def get_product_vars(self):
        data = {}
        product_actions = self.user.product_actions.prefetch_related(
            "product__topics"
        ).all()

        registered_actions = [pa for pa in product_actions if pa.type == "registered"]
        consumed_actions = [pa for pa in product_actions if pa.type == "consumed"]

        data.update(self._get_aggregated_topic_product_vars(product_actions))
        data.update(
            self._get_aggregated_action_product_vars(
                registered_actions, consumed_actions
            )
        )
        data.update(self._get_action_product_vars(registered_actions, consumed_actions))

        return data

    def get_fields(self):
        """
        TODO: This isn't part of reformating data for syncing with sailthru.  It
        is specific to the API request, not the user.  We should probably put it
        somewhere else.
        """
        data = {
            "keys": 1,
            "optout_email": 1,
        }
        return data

    def convert(self):
        if not self.user.email:
            raise ConversionError("Email is required for conversion")

        data = dict(
            (
                ("id", self.user.email),
                ("key", "email"),
                ("lists", self.get_list_subscriptions()),
                ("fields", self.get_fields()),
            )
        )

        if self.user.sailthru_optout:
            data["optout_email"] = self.user.sailthru_optout

        data["vars"] = dict(
            (
                ("email_domain", self.get_email_domain()),
                ("audb_last_modified_time", self.get_modified_time()),
                ("last_synced_time", self.get_sync_time()),
                ("sources", self.get_sources()),
            )
        )

        if {"first_name", "last_name"} & set(self.vars_to_sync):
            data["vars"]["name"] = self.get_name()

        if "procurement_subject" in self.vars_to_sync:
            data["vars"]["procurement_subject"] = self.get_procurement_subject()

        source = self.get_source()
        if source is not None:
            data["vars"]["source"] = source
            data["vars"]["source_signup_date"] = self.get_source_signup_date()

        data["vars"].update(self.get_one_to_one_fields())
        data["vars"].update(self.get_var_subscriptions())
        data["vars"].update(self.get_product_vars())

        return data
