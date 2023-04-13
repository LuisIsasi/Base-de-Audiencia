import copy
import datetime
import hashlib
from collections import defaultdict

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.formats import dateformat
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django_extensions.db.models import TimeStampedModel
from sailthru_sync import validators as st_validators

from core import fields


# querysets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class SubscriptionQuerySet(models.QuerySet):
    def can_unsubscribe(self):
        return self.filter(
            list__no_unsubscribe=False,
            active=True
        )


# managers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class AudbBaseManager(models.Manager):

    def validate_and_create(self, **kwargs):
        test_instance = self.model(**kwargs)
        test_instance.full_clean()
        return self.create(**kwargs)


class EmailChangeAudienceUserManager(AudbBaseManager):

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.exclude(models.Q(email="") | models.Q(email__isnull=True))
        return qs


class SubscriptionManager(AudbBaseManager):

    def unsubscribe_from_all(self, user, comment=None):
        subscriptions = user.subscriptions.can_unsubscribe()
        for subscription in subscriptions:
            subscription.unsubscribe(comment)


# models ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class AbstractValidationModel(models.Model):

    objects = AudbBaseManager()

    def validate_and_save(self):
        self.full_clean()
        self.save()

    class Meta:
        abstract = True


class List(TimeStampedModel, AbstractValidationModel):

    class Meta:
        ordering = ['slug']

    LIST_TYPE_CHOICES = (
        ('list', 'List'),  # TODO ? maybe add 'brand' as a choice ?
        ('newsletter', 'Newsletter'),
    )

    name = models.CharField(
        max_length=500,
        unique=True,
        null=False,
        blank=False,
        help_text="List name/description"
    )

    slug = fields.ListSlugField(
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        help_text="List slug: must be all-lowercase and underscore-separated"
    )

    type = models.CharField(
        max_length=255,
        choices=LIST_TYPE_CHOICES,
        null=False,
        blank=False
    )

    sync_externally = models.BooleanField(
        default=True,
        null=False,
        help_text="Sync this list with external services, _eg_ Sailthru."
    )

    no_unsubscribe = models.BooleanField(
        default=False,
        null=False,
        help_text=(
            "Current behavior: setting this to true will exempt this list "
            "from auto-unsubscribes that occur when a user opts out of all "
            "emails (e.g. Optout Basic / Optout All).  Explicit unsubscribes "
            "will still take effect, but that may be changed in the future."
        )
    )

    archived = models.BooleanField(
        default=False,
        null=False,
        help_text="Mark the list as archived/inactive."
    )

    @property
    def sailthru_list_name(self):
        if self.is_sailthru_list():
            return self.slug

        prefixes = ['newsletter_', 'custom_newsletter_', 'archive_newsletter_', ]
        for prefix in prefixes:
            if self.slug.startswith(prefix):
                return self.slug[len(prefix):]
        raise ValueError("Invalid value for slug")

    @property
    def sailthru_var_name(self):
        if self.is_sailthru_newsletter():
            return self.slug
        return 'list_' + self.slug

    def is_sailthru_newsletter(self):
        return self.type == 'newsletter'

    def is_sailthru_list(self):
        return self.type == 'list'

    def add_subscription_trigger(self, related_list, override_previous_unsubscribes):
        return SubscriptionTrigger.objects.validate_and_create(
            primary_list=self,
            related_list=related_list,
            override_previous_unsubscribes=override_previous_unsubscribes
        )

    def remove_subscription_trigger(self, related_list):
        return (
            SubscriptionTrigger
            .objects
            .get(primary_list=self, related_list=related_list)
            .delete()
        )

    def can_sync(self):
        return self.sync_externally and not self.archived

    def stats(self):
        return (
            '<a href="/core/list/{}/stats/">User Stats</a>'.format(self.pk) +
            ' | <a href="/core/subscriptionlog/?list_id={}">Subscription Log</a>'.format(self.pk)
        )
    stats.short_description = "User Data"
    stats.allow_tags = True

    def clean(self, *args, **kwargs):
        super(List, self).clean(*args, **kwargs)
        nl_prefixes = ["newsletter_", "archive_newsletter_", "custom_newsletter_"]
        if self.is_sailthru_list():
            for nl_prefix in nl_prefixes:
                if self.slug.startswith(nl_prefix):
                    msg = mark_safe(
                        "A list may not start with any of the following:<br/>" +
                        "<br/>".join(["'{}'".format(p) for p in nl_prefixes])
                    )
                    raise ValidationError({
                        "type": "",
                        "slug": msg,
                    })
        elif self.is_sailthru_newsletter():
            for nl_prefix in nl_prefixes:
                if self.slug.startswith(nl_prefix):
                    return
            msg = mark_safe(
                "A newsletter must start with one of:<br/>" +
                "<br/>".join(["'{}'".format(p) for p in nl_prefixes])
            )
            raise ValidationError({
                "type": "",
                "slug": msg,
            })
        else:
            raise ValidationError({
                "type": "Unable to determine type of list.",
            })

    def __str__(self):
        return self.slug if self.slug else ''


class AudienceUser(TimeStampedModel, AbstractValidationModel):
    OPTOUT_NONE = 'none'
    OPTOUT_ALL = 'all'
    OPTOUT_BASIC = 'basic'
    OPTOUT_BLAST = 'blast'  # Not implemented (by us)

    OPTOUT_MAP = {
        OPTOUT_NONE: 'None',
        OPTOUT_ALL: 'Optout (All)',
        OPTOUT_BASIC: 'Optout (Basic)',
        OPTOUT_BLAST: 'Optout (Blast)',
    }

    OPTOUT_OPTIONS = (
        (OPTOUT_NONE, OPTOUT_MAP[OPTOUT_NONE]),
        (OPTOUT_ALL, OPTOUT_MAP[OPTOUT_ALL]),
        (OPTOUT_BASIC, OPTOUT_MAP[OPTOUT_BASIC]),
        (OPTOUT_BLAST, OPTOUT_MAP[OPTOUT_BLAST]),
    )

    class Meta:
        ordering = ['email']
        verbose_name = 'User'

    email = fields.NormalizedEmailField(
        max_length=500,
        unique=True,
        null=True,
        blank=True,
        help_text="(Note that this field can be empty.)"
    )

    omeda_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="Omeda ID")

    sailthru_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Sailthru ID"
    )
    sailthru_optout = models.CharField(
        max_length=40, null=True, blank=True, choices=OPTOUT_OPTIONS
    )

    vars = JSONField(
        default=dict,
        blank=True,
        validators=[
            fields.vars_jsonfield_validator,
            st_validators.reserved_words_jsonfield_validator,
        ]
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if self.email is not None and not self.email.strip():
            # prevent empty-string emails while still allowing None/NULL emails,
            # which is what we want; setting blank=False on this model would not
            # accommodate this because of the way field validation works in that case
            self.email = None
        if self.vars is None:
            self.vars = {}
        super(AudienceUser, self).save(*args, **kwargs)

        if is_new:
            self._record_initial_optin()

    def _list_sub_or_unsub(self, list_slug, action, log_comment=None, log_action=None):
        if action not in ('subscribe', 'unsubscribe'):
            raise ValueError("action must be either 'subscribe' or 'unsubscribe'")
        is_active = action == 'subscribe'
        list_ = List.objects.get(slug=list_slug)
        log_override = {'comment': log_comment, 'action': log_action}

        try:
            subscription = self.subscriptions.get(list=list_)
            subscription.active = is_active
            subscription.log_override = log_override
            subscription.validate_and_save()
        except Subscription.DoesNotExist:
            subscription = self.subscriptions.validate_and_create(
                audience_user=self,
                list=list_,
                active=is_active,
                log_override=log_override
            )

        return subscription

    def disable_sync(self):
        self._sync_disabled = True

    def list_subscribe(self, list_slug, log_comment=None, log_action=None):
        return self._list_sub_or_unsub(list_slug, 'subscribe', log_comment, log_action)

    def list_unsubscribe(self, list_slug, log_comment=None, log_action=None):
        return self._list_sub_or_unsub(list_slug, 'unsubscribe', log_comment, log_action)

    @property
    def subscription_log(self):
        return SubscriptionLog.objects.select_related().filter(subscription__audience_user=self)

    @property
    def optout_display_name(self):
        try:
            return self.OPTOUT_MAP[self.sailthru_optout]
        except KeyError:
            return 'Not Set'

    def record_product_action(self, product_slug, action_type, timestamp, details=None):
        if details and not isinstance(details, type(list())):
            raise TypeError("'details' should be a list")

        product = Product.objects.get(slug=product_slug)

        try:
            action = self.product_actions.get(product__slug=product_slug, type=action_type)
            action.validate_and_save()  # so that we bump the 'modified' timestamp
        except ProductAction.DoesNotExist:
            action = ProductAction.objects.validate_and_create(
                audience_user=self, product=product, type=action_type, timestamp=timestamp
            )

        if details:
            for detail in details:
                ProductActionDetail.objects.validate_and_create(
                    product_action=action, description=detail, timestamp=timestamp
                )

        return action

    def _record_initial_optin(self):
        self.record_optout(
            AudienceUser.OPTOUT_NONE,
            'Initial opt in for new user',
            effective_date=timezone.now()
        )

    def record_optout(self, optout_value, comment, effective_date=None):
        """
        Adds a sailthru optout status to this user's optout history.  Values
        are not limited to actual optouts.  For example, an `optout_value` of
        'none' indicates user is not opted out)
        """

        optout_history = OptoutHistory.objects.validate_and_create(
            audience_user=self,
            sailthru_optout=optout_value,
            comment=comment,
            effective_date=effective_date
        )
        optout_history.save(update_user=False)

        self.reset_sailthru_optout()

    def reset_sailthru_optout(self):
        """
        Gets most recent optout status and caches it on AudienceUser object
        """
        most_recent_optout = self.optout_history.order_by('-effective_date')[0]
        self.sailthru_optout = most_recent_optout.sailthru_optout
        self.save()

        if self.sailthru_optout in (AudienceUser.OPTOUT_ALL, AudienceUser.OPTOUT_BASIC):
            Subscription.objects.unsubscribe_from_all(
                self,
                comment="unsubscribe triggered by sailthru optout (all/basic)"
            )

    @property
    def email_hash(self):
        if not self.email:
            return None
        hasher = hashlib.md5()
        hasher.update(self.email.encode('utf-8'))
        return hasher.hexdigest()

    def admin_view_created_date(self):
        # this is a work-around b/c Django admin does not want to display
        # fields with auto_now / auto_now_add
        return (
            dateformat.format(localtime(self.created), settings.DATETIME_FORMAT)
            if self.created else None
        )
    admin_view_created_date.short_description = "Created"

    def admin_view_modified_date(self):
        # this is a work-around b/c Django admin does not want to display
        # fields with auto_now / auto_now_add
        return (
            dateformat.format(localtime(self.modified), settings.DATETIME_FORMAT)
            if self.modified else None
        )
    admin_view_modified_date.short_description = "Modified"

    def list_view_sailthru_link(self):
        return (
            format_html(
                """
                <a target="_blank" href="https://my.sailthru.com/reports/user_lookup?id={}"
                >Sailthru profile</a>
                """,
                self.email
            )
            if self.email and self.sailthru_id else ''
        )
    list_view_sailthru_link.short_description = "View Sailthru Profile"

    def __str__(self):
        if self.email:
            return self.email
        if self.pk:
            return 'no email address [pk={pk}]'.format(pk=self.pk)
        return ''

    """
    TODO: we are still not considering Sailthru engagement in audb
    """


class EmailChangeAudienceUser(AudienceUser):
    objects = EmailChangeAudienceUserManager()

    class Meta:
        proxy = True
        verbose_name = 'user email'
        verbose_name_plural = 'users - change emails'


class UserSource(AbstractValidationModel):

    class Meta:
        ordering = ['-timestamp']

    audience_user = models.ForeignKey(
        AudienceUser,
        on_delete=models.CASCADE,
        null=False,
        related_name="source_signups"
    )
    name = models.CharField(
        max_length=500,
        null=False,
        help_text="Slug-like value identifying the source of the user sign-up"
    )
    timestamp = models.DateTimeField(auto_now_add=True, null=False)

    def __str__(self):
        return self.name if self.name else ''


class OptoutHistory(AbstractValidationModel):

    class Meta:
        ordering = ['-effective_date']

    audience_user = models.ForeignKey(
        AudienceUser,
        on_delete=models.CASCADE,
        null=False,
        related_name="optout_history"
    )

    sailthru_optout = models.CharField(
        max_length=40, null=False, blank=False, choices=AudienceUser.OPTOUT_OPTIONS
    )

    comment = models.TextField(
        null=False, blank=False, help_text="Explanatory supporting text."
    )

    created_date = models.DateTimeField(auto_now_add=True, null=False)
    effective_date = models.DateTimeField(default=timezone.now, null=False)

    def save(self, update_user=True, *args, **kwargs):
        super(OptoutHistory, self).save(*args, **kwargs)

        if update_user:
            self.audience_user.reset_sailthru_optout()


class UserVarsHistory(AbstractValidationModel):

    class Meta:
        ordering = ['-timestamp']

    audience_user = models.ForeignKey(
        AudienceUser,
        on_delete=models.CASCADE,
        null=False,
        related_name="vars_history"
    )

    vars = JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, null=False)


class VarKey(AbstractValidationModel):

    class Meta:
        ordering = ['type', 'key', ]
        verbose_name = 'Var'

    VARKEY_TYPE_CHOICES = (
        ('official', 'Official'),
        ('other', 'Other'),
    )

    key = models.CharField(
        max_length=500,
        unique=True,
        null=False,
        blank=False,
        help_text="Var name (may not contain spaces)",
        validators=[fields.varkey_validator, st_validators.reserved_words_validator],
    )

    type = models.CharField(
        max_length=255,
        choices=VARKEY_TYPE_CHOICES,
        null=False,
        blank=False
    )

    sync_with_sailthru = models.BooleanField(
        default=True,
        null=False,
        help_text="Sync this var with Sailthru; note that this will not have any retroactive "
                  "effect if changing this flag on an existing var."
    )

    def __str__(self):
        synced = 'synced' if self.sync_with_sailthru else 'not synced'
        return (
            "{} [{}] [{}]".format(self.key, self.type, synced)
            if (self.key and self.type)
            else ''
        )


class Subscription(TimeStampedModel, AbstractValidationModel):

    class Meta:
        ordering = ['list__slug']
        unique_together = ('audience_user', 'list')

    objects = SubscriptionManager.from_queryset(SubscriptionQuerySet)()

    audience_user = models.ForeignKey(
        AudienceUser, null=False, related_name="subscriptions"
    )

    list = models.ForeignKey(List, null=False, related_name="subscriptions")

    active = models.BooleanField(
        default=True,
        null=False,
        help_text="Indicates whether the user is subscribed/opted-in to the list"
    )

    log_override = JSONField(
        default=dict,
        blank=True,
        help_text="JSON object containing values that supersede those that would "
                  "otherwise be used when creating the on-save SubscriptionLog entry"
    )

    def subscription_log_html(self):
        return format_html_join(
            mark_safe('<br/>'), '{}', ((str(x),) for x in self.log.all())
        )
    subscription_log_html.short_description = u'Log'

    def list_type(self):
        return self.list.type if self.list else ''
    list_type.short_description = u'Type'

    def __str__(self):
        if self.audience_user and self.list:
            status = "subscribed to" if self.active else "unsubscribed from"
            return "{} is {} {}".format(self.audience_user, status, self.list)
        else:
            return ''

    def clean(self):
        if (not self.pk) and self.list and self.list.archived:
            raise ValidationError("Cannot add a user to an archived list.")

        subscription_log_actions = [x[0] for x in SubscriptionLog.SUBSCRIPTION_ACTION_CHOICES]
        if self.log_override and self.log_override.get('action'):
            if self.log_override['action'] not in subscription_log_actions:
                raise ValidationError("Unknown subscription log override action")

        super(Subscription, self).clean()

    def unsubscribe(self, comment=None):
        self.active = False
        if comment:
            self.log_override = {
                "comment": comment
            }
        self.save()

    def save(self, *args, **kwargs):
        log_override = copy.deepcopy(self.log_override) if self.log_override else {}
        self.log_override = {}  # we never actually want to save this to the db

        super(Subscription, self).save(*args, **kwargs)

        if log_override.get('action', None):
            action = log_override['action']
        else:
            action = "subscribe" if self.active else "unsubscribe"
        comment = log_override.get('comment', None)

        SubscriptionLog.objects.validate_and_create(
            subscription=self, action=action, comment=comment
        )


class SubscriptionLog(AbstractValidationModel):

    SUBSCRIPTION_ACTION_CHOICES = (
        ('subscribe', 'subscribe'),
        ('unsubscribe', 'unsubscribe'),

        ('trigger', 'trigger'),  # subscriptions triggered by SubscriptionTriggers
        ('update', 'update'),  # for things like legacy data imports or via-Admin updates
    )

    action = models.CharField(
        max_length=255,
        choices=SUBSCRIPTION_ACTION_CHOICES,
        null=False,
        blank=False
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        null=False,
        related_name="log",
        db_index=True
    )

    comment = models.TextField(
        blank=True, null=True, help_text="Explanatory supporting text."
    )

    timestamp = models.DateTimeField(auto_now_add=True, null=False, unique=False, db_index=True)

    def __str__(self):
        if self.action and self.subscription and self.timestamp:
            comment = ' / {}'.format(self.comment) if self.comment else ''
            return '[{}] {} -> {}{}'.format(
                dateformat.format(localtime(self.timestamp), settings.DATETIME_FORMAT),
                self.action,
                self.subscription.list,
                comment
            )
        return ''


class SubscriptionTrigger(AbstractValidationModel):

    class Meta:
        unique_together = ('primary_list', 'related_list')

    primary_list = models.ForeignKey(List, null=False, related_name="subscription_triggers")
    related_list = models.ForeignKey(List, null=False, related_name="+")

    override_previous_unsubscribes = models.BooleanField(
        default=False,
        null=False,
        help_text="Should this trigger ignore situations where the user has previously "
                  "unsubscribed from the list in question? If checked, "
                  "previously-unsubscribed users will be re-subscribed."
    )

    def clean(self):
        if (self.primary_list is not None) and (self.primary_list == self.related_list):
            raise ValidationError("A list cannot trigger itself.")
        super(SubscriptionTrigger, self).clean()


class Product(TimeStampedModel, AbstractValidationModel):

    class Meta:
        ordering = ['name']

    PRODUCT_BRAND_CHOICES = (
        ('Defense One', 'Defense One'),
        ('Govexec', 'Govexec'),
        ('Nextgov', 'Nextgov'),
        ('Route Fifty', 'Route Fifty'),
        ('Federal Soup', 'Federal Soup'),
        ('FCW', 'FCW'),
        ('Washington Technology', 'Washington Technology'),
        ('GCN', 'GCN'),
        ('Defense Systems', 'Defense Systems'),
        ('GMarkU', 'GMarkU'),
        ('Military Periscope', 'Military Periscope'),
        ('Forecast International', 'Forecast International'),
        ('The Atlas Market Edge', 'The Atlas Market Edge'),
    )

    PRODUCT_TYPE_CHOICES = (
        ('app', 'App'),
        ('asset', 'Asset'),
        ('event', 'Event'),
        ('questionnaire', 'Questionnaire'),
    )

    TYPE_TO_CONSUMED_VERB = {
        'app': 'used',
        'asset': 'downloaded',
        'event': 'attended',
        'questionnaire': 'completed',
    }

    # only one option for now so just making everything return registered
    TYPE_TO_REGISTERED_VERB = defaultdict(lambda: "registered")

    name = models.CharField(
        max_length=500,
        unique=True,
        null=False,
        blank=False,
        help_text="Product name/description"
    )

    slug = fields.ProductSlugField(
        max_length=500,
        unique=True,
        null=False,
        blank=False,
        help_text="Product slug: must be all-lowercase and may optionally contain numbers; "
                  "slugs cannot be changed after initial creation because they are used to "
                  "update external sources like Sailthru."
    )

    brand = models.CharField(
        max_length=255,
        choices=PRODUCT_BRAND_CHOICES,
        null=False,
        blank=False
    )

    type = models.CharField(
        max_length=255,
        choices=PRODUCT_TYPE_CHOICES,
        null=False,
        blank=False,
        help_text="Cannot be changed after initial creation because the product type is used "
                  "to update external sources like Sailthru."
    )

    subtypes = models.ManyToManyField('ProductSubtype')
    topics = models.ManyToManyField('ProductTopic')

    @classmethod
    def product_types(cls):
        return [t[0] for t in cls.PRODUCT_TYPE_CHOICES]

    @classmethod
    def consumed_verb_for_type(cls, product_type):
        return cls.TYPE_TO_CONSUMED_VERB[product_type]

    @classmethod
    def registered_verb_for_type(cls, product_type):
        return cls.TYPE_TO_REGISTERED_VERB[product_type]

    @property
    def consumed_verb(self):
        return self.consumed_verb_for_type(self.type)

    @property
    def registered_verb(self):
        return self.registered_verb_for_type(self.type)

    def csv_columns_html(self):
        return format_html(
            """
            product[{type}_{slug}_{registered_verb}]<br/>
            product[{type}_{slug}_{registered_verb}_details]<br/>
            product[{type}_{slug}_{consumed_verb}]<br/>
            product[{type}_{slug}_{consumed_verb}_details]<br/>
            """
            .format(
                type=self.type,
                slug=self.slug,
                registered_verb=self.registered_verb,
                consumed_verb=self.consumed_verb
            )
        )
    csv_columns_html.short_description = 'CSV columns'

    def sailthru_vars_html(self):
        return format_html(
            """
            {type}_{slug}_{registered_verb}_time<br/>
            {type}_{slug}_{registered_verb}_details<br/>
            {type}_{slug}_{consumed_verb}_time<br/>
            {type}_{slug}_{consumed_verb}_details<br/>
            """
            .format(
                type=self.type,
                slug=self.slug,
                registered_verb=self.registered_verb,
                consumed_verb=self.consumed_verb
            )
        )
    sailthru_vars_html.short_description = 'Sailthru vars'

    def __str__(self):
        if self.name and self.type:
            return "{} [{}]".format(self.name, self.type)
        return ''


class ProductTopic(AbstractValidationModel):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=1000,
        unique=True,
        null=False,
        blank=False,
        help_text="Product topic"
    )

    def __str__(self):
        return self.name if self.name else ''


class ProductSubtype(AbstractValidationModel):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=1000,
        unique=True,
        null=False,
        blank=False,
        help_text="Product subtype"
    )

    def __str__(self):
        return self.name if self.name else ''


class ProductAction(TimeStampedModel, AbstractValidationModel):

    class Meta:
        ordering = ['-timestamp']
        unique_together = (('audience_user', 'product', 'type'),)

    ACTION_TYPE_CHOICES = (
        ('consumed', 'consumed'),
        ('registered', 'registered'),
    )

    audience_user = models.ForeignKey(AudienceUser, null=False, related_name="product_actions")

    product = models.ForeignKey(Product, null=False, related_name="+")

    timestamp = models.DateTimeField(auto_now_add=False, auto_now=False, null=False)

    type = models.CharField(
        max_length=255,
        choices=ACTION_TYPE_CHOICES,
        null=False,
        blank=False
    )

    @property
    def product_slug(self):
        return self.product.slug if self.product else ''

    @property
    def sailthru_consumed_var(self):
        context = {
            'type': self.product.type,
            'slug': self.product.slug,
            'verb': self.product.consumed_verb,
        }
        var = "{type}_{slug}_{verb}_time".format(**context)
        return var

    @property
    def sailthru_registered_var(self):
        context = {
            'type': self.product.type,
            'slug': self.product.slug,
            'verb': self.product.registered_verb,
        }
        var = "{type}_{slug}_{verb}_time".format(**context)
        return var

    @property
    def sailthru_consumed_details_var(self):
        context = {
            'type': self.product.type,
            'slug': self.product.slug,
            'verb': self.product.consumed_verb,
        }
        var = "{type}_{slug}_{verb}_details".format(**context)
        return var

    @property
    def sailthru_registered_details_var(self):
        context = {
            'type': self.product.type,
            'slug': self.product.slug,
            'verb': self.product.registered_verb,
        }
        var = "{type}_{slug}_{verb}_details".format(**context)
        return var

    @property
    def sailthru_consumed_value(self):
        return self.timestamp.timestamp()

    @property
    def sailthru_registered_value(self):
        return self.timestamp.timestamp()

    @property
    def sailthru_consumed_details_value(self):
        return [d.description for d in self.details.all()] or 0

    @property
    def sailthru_registered_details_value(self):
        return [d.description for d in self.details.all()] or 0

    def details_html(self):
        details_tuple = (
            (dateformat.format(localtime(x.timestamp), settings.DATETIME_FORMAT), x.description)
            for x in self.details.all()
        )
        return format_html_join(mark_safe('<br/>'), '[{}] {}', details_tuple)
    details_html.short_description = u'Details'

    def clean(self):
        if self.pk is not None:
            original = ProductAction.objects.get(pk=self.pk)
            if original.timestamp != self.timestamp:
                raise ValidationError({"timestamp": "Timestamps cannot be modified."})
        super(ProductAction, self).clean()

    def __str__(self):
        if self.product and self.product.name and self.type:
            return "{} - {}".format(self.product.name, self.type)
        else:
            return ""


class ProductActionDetail(TimeStampedModel, AbstractValidationModel):
    class Meta:
        ordering = ['-id']

    product_action = models.ForeignKey(ProductAction, null=False, related_name="details")
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=False, null=False)

    def __str__(self):
        return self.description if self.description else ""


class AthenaContentType(AbstractValidationModel):
    """
    This table is synonymous with the govexec.django_content_type table.
    It requires a manual sync when new content types are added to govexec.django_content_type.
    """

    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="This is the combination of the app label and model name from the govexec.django_content_type table. E.g. post_manager.post"
    )


class AthenaContentMetadata(AbstractValidationModel):
    """
    This table contains data related to entries in the govexec.post_manager_content table. All previously created content exists
    in this audb table, and any newly created content (in govexec.post_manager_content) will automatically be added to this table via an API call.
    """

    class Meta:
        verbose_name_plural = "Athena Content Metadata"

    athena_content_id = models.IntegerField(
        unique=True,
        null=False,
        db_index=True
    )

    athena_content_type = models.ForeignKey(
        AthenaContentType,
        related_name="athena_content_metadata",
        on_delete=models.DO_NOTHING,
        null=False,
        db_index=True
    )

    date_published = models.DateTimeField(
        'Publish date',
        help_text='The date and time the post went live.',
        blank=True,
        null=True
    )

    date_created = models.DateTimeField(
        help_text='This date the original post was created in the govexec database.',
        null=False
    )

    title = models.CharField(max_length=255)

    slug = models.SlugField(
        max_length=255,
        help_text='The URL name of the content, based off title.'
    )

    absolute_url = models.URLField(
        "Absolute URL",
        max_length=500
    )

    canonical_url = models.URLField(
        "Canonical URL",
        max_length=500,
        blank=True,
        null=True
    )

    site_name = models.CharField(
        max_length=25
    )

    organization = models.SlugField(
        max_length=255,
        help_text='The URL name of the organization associated with the content.'
    )

    authors = ArrayField(
        models.CharField(max_length=200),
        help_text='The author(s) associated with the content.',
        null=True,
        blank=True
    )

    categories = JSONField(
        help_text='The primary category slug and slugs for any secondary categories associated with the content.',
        default=dict,
        null=False
    )

    topics = ArrayField(
        models.CharField(max_length=75),
        help_text='The topic slugs associated with the content.',
        null=True,
        blank=True
    )

    keywords = ArrayField(
        models.CharField(max_length=100),
        help_text='The keywords associated with the content. The same keyword may also exist in the interests field.',
        null=True,
        blank=True
    )

    interests = ArrayField(
        models.CharField(max_length=100),
        help_text='The (sailthru) interests associated with the content. The same interest may also exist in the keywords field.',
        null=True,
        blank=True
    )

    is_sponsored_content = models.BooleanField(
        help_text="""Signifies whether the content is associated with a primary category that is a sponsored category.
                     Note: This is not the same as the is_sponsored field in govexec.post_manager_content. It is the return
                     value of the is_sponsored_content method in the post_manager.Content class in the govexec codebase.""",
        default=False
    )


class UserContentHistory(AbstractValidationModel):

    class Meta:
        verbose_name_plural = "User Content History"

    email = models.EmailField(
        max_length=500,
        null=False,
        db_index=True
    )

    athena_content_metadata = models.ForeignKey(
        AthenaContentMetadata,
        to_field="athena_content_id",
        related_name="user_content_history",
        on_delete=models.DO_NOTHING,
        null=False,
        db_index=True
    )

    timestamp = models.DateTimeField(auto_now_add=True, null=False)

    referrer = fields.ReferrerField(blank=True, null=True, max_length=500)
