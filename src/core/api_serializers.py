import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from rest_framework import serializers, validators
from rest_framework.fields import SkipField, set_value
from rest_framework.serializers import ValidationError

from .fields import (
    list_slug_validator,
    normalized_email_validator,
    product_slug_validator,
)
from . import models as m


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.

    ---Note from BS---
    Modified version of copy-paste from the DRF documentation:
    http://www.django-rest-framework.org/api-guide/serializers/#example
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        fields_param = self.context["request"].query_params.get("fields", None)
        if fields_param is not None:
            fields = fields_param.split(",")
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class AthenaContentMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.AthenaContentMetadata
        fields = "__all__"


class ReferrerField(serializers.URLField):
    """
    Intended to make `referrer` more inclusive.
    See also `core.fields.ReferrerField`.
    """

    def __init__(self, *args, **kwargs):
        # bypassing URLField's inflexible init
        super(serializers.URLField, self).__init__(*args, **kwargs)

        validator = URLValidator(
            message=self.error_messages["invalid"],
            schemes=[
                "http",
                "https",
                "android-app",
            ],
        )
        self.validators.append(validator)


class UserContentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.UserContentHistory
        fields = "__all__"

    referrer = ReferrerField(allow_blank=True, required=False, max_length=500)

    def to_internal_value(self, data):
        referrer = data.get("referrer", "")
        max_length = m.UserContentHistory._meta.get_field("referrer").max_length
        if len(referrer) > max_length:
            data["referrer"] = referrer[0:max_length]

        return super(UserContentHistorySerializer, self).to_internal_value(data)


class CompactListSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.List
        fields = ("slug",)


class ProductSubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductSubtype
        fields = (
            "id",
            "name",
        )


class ProductTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductTopic
        fields = (
            "id",
            "name",
        )


class NestedProductSubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductSubtype
        fields = ("name",)

    def to_internal_value(self, data):
        return data  # bypass validation b/c we do it in the Product creation


class NestedProductTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductTopic
        fields = ("name",)

    def to_internal_value(self, data):
        return data  # bypass validation b/c we do it in the Product creation


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Product
        fields = (
            "id",
            "name",
            "slug",
            "brand",
            "type",
            "subtypes",
            "topics",
            "consumed_verb",
            "registered_verb",
        )
        read_only_fields = (
            "subtypes",
            "topics",
            "consumed_verb",
            "registered_verb",
        )

    slug = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
        validators=[
            product_slug_validator,
            validators.UniqueValidator(queryset=m.Product.objects.all()),
        ],
    )

    subtypes = NestedProductSubtypeSerializer(many=True, read_only=False, required=True)
    topics = NestedProductTopicSerializer(many=True, read_only=False, required=True)

    def create(self, validated_data):
        subtypes = [
            m.ProductSubtype.objects.get(name=x["name"])
            for x in validated_data.pop("subtypes", [])
        ]
        topics = [
            m.ProductTopic.objects.get(name=x["name"])
            for x in validated_data.pop("topics", [])
        ]

        product = m.Product.objects.validate_and_create(**validated_data)
        for subtype in subtypes:
            product.subtypes.add(subtype)
        for topic in topics:
            product.topics.add(topic)

        return product

    def is_valid(self, raise_exception=False):
        errors = {}

        if not self.initial_data.get("subtypes", []):
            errors["subtypes"] = ["Must provide one or most product subtypes."]
        if not self.initial_data.get("topics", []):
            errors["topics"] = ["Must provide one or most product topics."]

        for product_subtype in self.initial_data.get("subtypes", []):
            if "name" not in product_subtype:
                errors["subtypes"] = ['Must specify "name".']
            else:
                try:
                    m.ProductSubtype.objects.get(name=product_subtype["name"])
                except m.ProductSubtype.DoesNotExist:
                    errors["subtypes"] = [
                        "Unknown product subtype: {}".format(product_subtype["name"])
                    ]

        for product_topic in self.initial_data.get("topics", []):
            if "name" not in product_topic:
                errors["topics"] = ['Must specify "name".']
            else:
                try:
                    m.ProductTopic.objects.get(name=product_topic["name"])
                except m.ProductTopic.DoesNotExist:
                    errors["topics"] = [
                        "Unknown product topic: {}".format(product_topic["name"])
                    ]

        try:
            super_is_valid = super(ProductSerializer, self).is_valid(
                raise_exception=raise_exception
            )
        except serializers.ValidationError as e:
            errors.update(e.detail)

        if errors:
            raise serializers.ValidationError(errors)

        return super_is_valid

    def update(self, instance, validated_data):  # pragma: no cover
        # in practice this code should be unreachable b/c the
        # view should never allow things to get this far
        raise NotImplementedError(
            "Products currently cannot be updated. "
            "Support for this can be added when neccessray."
        )


class SubscriptionTriggerSerializerCompact(serializers.ModelSerializer):
    class Meta:
        model = m.SubscriptionTrigger
        fields = (
            "id",
            "related_list",
            "override_previous_unsubscribes",
        )

    related_list = CompactListSerializer(required=True, many=False)


class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.List
        fields = (
            "id",
            "created",
            "modified",
            "name",
            "slug",
            "type",
            "sync_externally",
            "archived",
            "subscription_triggers",
        )

    slug = serializers.CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
        validators=[
            list_slug_validator,
            validators.UniqueValidator(queryset=m.List.objects.all()),
        ],
    )

    subscription_triggers = SubscriptionTriggerSerializerCompact(
        many=True, read_only=True, required=False
    )


class SubscriptionTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.SubscriptionTrigger

    primary_list = ListSerializer()
    related_list = ListSerializer()

    def to_internal_value(self, data):
        if not data.get("related_list_slug", None):
            raise ValidationError({"related_list_slug": "This field is required."})
        if not data.get("primary_list_slug", None):
            raise ValidationError({"primary_list_slug": "This field is required."})
        if data.get("override_previous_unsubscribes", None) is None:
            raise ValidationError(
                {"override_previous_unsubscribes": "This field is required."}
            )

        try:
            related_list = m.List.objects.get(slug=data["related_list_slug"])
        except m.List.DoesNotExist:
            raise ValidationError({"related_list_slug": "Related list does not exist."})
        try:
            primary_list = m.List.objects.get(slug=data["primary_list_slug"])
        except m.List.DoesNotExist:
            raise ValidationError({"primary_list_slug": "Primary list does not exist."})

        test_instance = m.SubscriptionTrigger.objects.model(
            primary_list=primary_list,
            related_list=related_list,
            override_previous_unsubscribes=data["override_previous_unsubscribes"],
        )
        try:
            test_instance.full_clean()
        except Exception as e:
            raise ValidationError(e.message_dict)

        return {
            "primary_list": primary_list,
            "related_list": related_list,
            "override_previous_unsubscribes": data["override_previous_unsubscribes"],
        }

    def create(self, validated_data):
        return m.SubscriptionTrigger.objects.validate_and_create(
            primary_list=validated_data["primary_list"],
            related_list=validated_data["related_list"],
            override_previous_unsubscribes=validated_data[
                "override_previous_unsubscribes"
            ],
        )

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "We do not have a use case for this yet."
        )  # pragma: no cover


class UserSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.UserSource
        fields = (
            "name",
            "timestamp",
        )

    timestamp = serializers.DateTimeField(required=False)


class UserVarsHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.UserVarsHistory
        fields = (
            "vars",
            "timestamp",
        )


class OptoutHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.OptoutHistory
        depth = 0
        fields = (
            "id",
            "effective_date",
            "created_date",
            "sailthru_optout",
            "comment",
            "audience_user",
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Subscription
        depth = 1
        fields = (
            "id",
            "created",
            "modified",
            "active",
            "list",
        )

    def to_internal_value(self, data):
        ret = {}

        ret["log_override"] = data.get("log_override", None)

        if data.get("active", None) is None:
            raise ValidationError({"active": "This field is required."})
        ret["active"] = data["active"]

        if self.instance:
            ret["list"] = self.instance.list
            ret["audience_user"] = self.instance.audience_user
            if ret["log_override"] and ret["log_override"].get("action"):
                test_sub_log = m.SubscriptionLog.objects.model(
                    action=ret["log_override"]["action"],
                    subscription=self.instance,
                    comment=ret["log_override"].get("comment"),
                )
                try:
                    test_sub_log.full_clean()
                except Exception as e:
                    raise ValidationError(e.message_dict)
        else:
            if not data.get("list", None):
                raise ValidationError({"list": "This field is required."})
            try:
                ret["list"] = m.List.objects.get(slug=data["list"])
            except m.List.DoesNotExist:
                raise ValidationError({"list": "Does not exist."})
            try:
                ret["audience_user"] = m.AudienceUser.objects.get(
                    pk=data["audienceuser_pk"]
                )
            except m.AudienceUser.DoesNotExist:
                raise ValidationError({"audience_user": "Does not exist."})

            test_instance = m.Subscription.objects.model(
                audience_user=ret["audience_user"],
                list=ret["list"],
                active=ret["active"],
                log_override=ret["log_override"],
            )
            try:
                test_instance.full_clean()
            except Exception as e:
                raise ValidationError(e.message_dict)

        return ret


class ProductActionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductActionDetail
        fields = (
            "description",
            "timestamp",
        )


class ProductActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ProductAction
        depth = 1
        fields = (
            "id",
            "product",
            "type",
            "timestamp",
            "created",
            "modified",
            "details",
        )

    details = ProductActionDetailSerializer(many=True, read_only=True)

    def to_internal_value(self, data):
        ret = {}
        errors = {}

        if "details" in data:
            if not isinstance(data["details"], list):
                raise ValidationError({"details": ["Expected a list."]})
            ret["details"] = data["details"]

        for field_name in ("type", "timestamp"):
            field = self.fields[field_name]
            assert (
                getattr(self, "validate_{}".format(field_name), None) is None
            ), "unexpected field validation method for {}".format(field_name)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:  # pragma: no cover
                errors[field.field_name] = list(exc.messages)  # pragma: no cover
            except SkipField:  # pragma: no cover
                pass  # pragma: no cover
            else:
                set_value(ret, field.source_attrs, validated_value)

        if "details" in ret and ret.get("timestamp", None):
            # preserve the original timestamp for future use with product action details
            ret["_details_timestamp"] = ret["timestamp"]

        if self.instance:
            ret["product"] = self.instance.product
            ret["audience_user"] = self.instance.audience_user
            ret["type"] = self.instance.type
            ret[
                "timestamp"
            ] = self.instance.timestamp  # timestamps can never be modified
        else:
            if not data.get("product", None):
                errors["product"] = ["This field is required."]
            else:
                try:
                    ret["product"] = m.Product.objects.get(slug=data["product"])
                except m.Product.DoesNotExist:
                    errors["product"] = [
                        "Product does not exist: {}".format(data["product"])
                    ]
            try:
                ret["audience_user"] = m.AudienceUser.objects.get(
                    pk=data["audienceuser_pk"]
                )
            except m.AudienceUser.DoesNotExist:
                errors["audience_user"] = ["This field is required."]

        if errors:
            raise ValidationError(errors)

        return ret

    def create(self, validated_data):
        details = validated_data.pop("details", [])
        details_timestamp = validated_data.pop("_details_timestamp", None)
        product_action = m.ProductAction.objects.validate_and_create(**validated_data)
        for detail in details:
            m.ProductActionDetail.objects.validate_and_create(
                product_action=product_action,
                description=detail,
                timestamp=details_timestamp,
            )
        return product_action

    def update(self, instance, validated_data):
        details = validated_data.pop("details", [])
        details_timestamp = validated_data.pop("_details_timestamp", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.validate_and_save()
        for detail in details:
            m.ProductActionDetail.objects.validate_and_create(
                product_action=instance, description=detail, timestamp=details_timestamp
            )
        return m.ProductAction.objects.get(pk=instance.pk)  # to get the latest stuff


class AudienceUserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = m.AudienceUser

        read_only_fields = (
            "email_hash",
            "sailthru_optout",
            "product_actions",
            "source_signups",
            "vars_history",
            "subscriptions",
            "subscription_log",
        )

        fields = (
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
            "sailthru_optout",
            "subscriptions",
            "subscription_log",
            "product_actions",
        )

    email = serializers.EmailField(
        allow_null=True,
        required=False,
        validators=[
            normalized_email_validator,
            validators.UniqueValidator(queryset=m.AudienceUser.objects.all()),
        ],
    )

    email_hash = serializers.CharField(read_only=True)

    subscriptions = SubscriptionSerializer(many=True, read_only=True)

    source_signups = UserSourceSerializer(many=True, read_only=False, required=False)

    vars_history = UserVarsHistorySerializer(many=True, read_only=True)

    subscription_log = serializers.ListField(
        child=serializers.CharField(), required=False, read_only=True
    )

    product_actions = ProductActionSerializer(many=True, read_only=True)

    def create(self, validated_data):
        source_signups = validated_data.pop("source_signups", [])
        user = m.AudienceUser.objects.validate_and_create(**validated_data)

        for ss in source_signups:
            user_source = user.source_signups.validate_and_create(
                audience_user=user, name=ss["name"]
            )
            if "timestamp" in ss:
                user_source.timestamp = ss["timestamp"]
                user_source.validate_and_save()

        return user

    def update(self, instance, validated_data):
        source_signups = validated_data.pop("source_signups", [])
        for ss in source_signups:
            user_source = instance.source_signups.validate_and_create(
                audience_user=instance, name=ss["name"]
            )
            if "timestamp" in ss:
                user_source.timestamp = ss["timestamp"]
                user_source.validate_and_save()

        # vars updating should be additive: we do not supplant the vars bucket wholesale,
        # but instead just add new vars or update existing ones
        instance.vars = self._update_vars(instance, validated_data.pop("vars", {}))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.validate_and_save()

        # IMPORTANT that we grab the instance from the db again (refresh_from_db() does
        # not do the trick); otherwise the source_signups will be stale when new ones
        # have been added in this method -- see above
        return m.AudienceUser.objects.get(pk=instance.pk)

    @staticmethod
    def _update_vars(instance, new_vars):
        old_vars = copy.deepcopy(instance.vars)
        for k, v in new_vars.items():
            old_vars[k] = v
        return old_vars


class VarKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.VarKey
        fields = (
            "id",
            "key",
            "type",
            "sync_with_sailthru",
        )
