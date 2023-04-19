# -*- coding: UTF-8 -*-

import json
import csv
import datetime

from celery.utils.log import get_task_logger
from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import TO_FIELD_VAR, csrf_protect_m
from django.contrib.admin.utils import get_deleted_objects, unquote
from django.contrib.postgres.fields import JSONField
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.admin.filters import DateFieldListFilter
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, models, router, transaction
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string as django_render_to_string
from django.template.response import SimpleTemplateResponse
from django.utils.encoding import force_text
from django.utils.html import escape, format_html
from django.utils.http import quote_plus
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils import timezone
from django.core.paginator import Paginator
from sailthru_sync import converter as sync_converter
from sailthru_sync import models as sync_models
from sailthru_sync.converter.errors import ConversionError
from sailthru_sync.errors import SailthruErrors
from sailthru_sync.tasks import sync_user_basic
from sailthru_sync.utils import sailthru_client
from sailthru_sync.validators import reserved_words_validator
import sentry_sdk


from . import fields
from . import models as m
from .widgets import DecomposedKeyValueJSONWidget


# TODO: vars history -- how/where to display


sync_logger = get_task_logger("sailthru_sync.tasks")


class UserSourceInline(admin.TabularInline):
    can_delete = False
    extra = 0
    fields = (
        "name",
        "timestamp",
    )
    model = m.UserSource
    readonly_fields = (
        "name",
        "timestamp",
    )
    verbose_name_plural = "Source Signups"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SubscriptionInline(admin.TabularInline):
    can_delete = False
    extra = 0
    fields = (
        "list",
        "list_type",
        "active",
        "subscription_log_html",
    )
    model = m.Subscription
    readonly_fields = (
        "list_type",
        "subscription_log_html",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super(SubscriptionInline, self)
            .get_queryset(request)
            .select_related("list", "audience_user")
            .prefetch_related("log")
        )


class ProductActionInline(admin.TabularInline):
    can_delete = False
    extra = 0
    model = m.ProductAction
    readonly_fields = (
        "product",
        "product_slug",
        "type",
        "timestamp",
        "modified",
        "details_html",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super(ProductActionInline, self)
            .get_queryset(request)
            .select_related("product")
            .prefetch_related("details")
        )


class AudienceUserForm(forms.ModelForm):
    class Meta:
        model = m.AudienceUser
        fields = "__all__"  # this is ignored b/c fields are defined on the ModelAdmin
        help_texts = {
            "admin_view_created_date": "Date the user was created in the Audience Database "
            "(post-MarkLogic transition)",
            "admin_view_modified_date": "Date the user was modified in the Audience Database "
            "(post-MarkLogic transition)",
        }

    def clean_vars(self):
        cleaned_data = self.cleaned_data.get("vars", {})
        if cleaned_data:
            dupe_keys = [
                x
                for x in cleaned_data.keys()
                if DecomposedKeyValueJSONWidget.dupe_key_mangling_regex.match(x)
            ]
            multi_word_keys = [x for x in cleaned_data.keys() if len(x.split()) > 1]
            errors = []
            if dupe_keys:
                errors.append("You attempted to add a var that already exists.")
            if multi_word_keys:
                errors.append("You attempted to add a var with spaces.")
            try:
                for key in cleaned_data.keys():
                    if key not in dupe_keys:
                        reserved_words_validator(key)
            except forms.ValidationError as e:
                errors.append(e.message)
            if errors:
                raise forms.ValidationError(mark_safe("<br/>".join(errors)))
            fields.vars_jsonfield_validator(cleaned_data)
        return cleaned_data


class DeleteAudienceUserAdminForm(forms.ModelForm):
    class Meta:
        model = m.AudienceUser
        fields = ("id",)

    def clean(self, *args, **kwargs):
        cleaned = super().clean(*args, **kwargs)
        if not settings.SAILTHRU_SYNC_ENABLED:
            return cleaned
        self._obtain_sync_lock()
        data = self._get_sync_data()
        response = self._sync_to_sailthru(data)
        self._check_response_ok(response)
        self._delete_sync_lock()
        return cleaned

    def _get_sync_data(self):
        try:
            sync_logger.debug(
                "Delete user (%s): converting user data to sailthru format.",
                str(self.instance.pk),
            )

            converter = sync_converter.AudienceUserToSailthruDelete(self.instance)
            return converter.convert()
        except ConversionError as e:
            msg = "Problem occured during data conversion for sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.error("Delete user (%s): " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(msg)

    def _sync_to_sailthru(self, data):
        try:
            sync_logger.debug(
                "Delete user (%s): Posting data to sailthru.", str(self.instance.pk)
            )
            response = sailthru_client().api_post("user", data)
            return response
        except Exception as e:
            msg = "Problem occured during request to Sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.error("Delete user (%s): " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(msg)

    def _check_response_ok(self, response):
        if not response.is_ok():
            error_code = response.get_error().get_error_code()
            is_invalid_email = error_code == SailthruErrors.INVALID_EMAIL

            can_ignore = not self.instance.sailthru_id and is_invalid_email
            if can_ignore:
                return
            msg = "Sailthru rejected request to delete user."
            failure = sync_models.SyncFailure.objects.from_sailthru_error_response(
                msg, self.instance, response
            )
            sync_logger.error("Delete user (%s): " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(failure.get_admin_anchor())
        try:
            response_data = response.get_body()
            response_data["keys"]["email"]
        except KeyError:
            msg = "Sailthru response missing expected values."
            failure = sync_models.SyncFailure.objects.from_sailthru_response(
                msg, self.instance, response
            )
            sync_logger.error("Delete user (%s): " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(failure.get_admin_anchor())

    def _delete_sync_lock(self):
        with transaction.atomic():
            self._sync_lock.delete()

    def _obtain_sync_lock(self):
        try:
            with transaction.atomic():
                self._aud_user = m.AudienceUser.objects.get(pk=self.instance.pk)
            lock = sync_models.SyncLock(locked_instance=self._aud_user)
            with transaction.atomic():
                lock.save()
        except m.AudienceUser.DoesNotExist:
            raise forms.ValidationError("This user has already been deleted.")
        except IntegrityError:
            raise forms.ValidationError(
                "This user is currently locked--preventing syncing with Sailthru."
            )
        self._sync_lock = lock


class AudienceUserAdmin(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("core/admin/css/audienceuser.css",),
        }

    form = AudienceUserForm
    formfield_overrides = {JSONField: {"widget": DecomposedKeyValueJSONWidget}}
    inlines = (
        SubscriptionInline,
        ProductActionInline,
        UserSourceInline,
    )
    list_display = ["email", "modified", "list_view_sailthru_link"]
    search_fields = ("email",)

    def get_fields(self, request, obj=None):
        include_fields = ["email", "sailthru_id", "vars", "omeda_id"]
        if obj:
            include_fields = [
                "readonly_sailthru_optout",
            ] + include_fields
            include_fields.extend(
                [
                    "admin_view_created_date",
                    "admin_view_modified_date",
                ]
            )
        return include_fields

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                "readonly_sailthru_optout",
                "email",
                "omeda_id",
                "admin_view_created_date",
                "admin_view_modified_date",
            )
        return ("omeda_id",)

    def readonly_sailthru_optout(self, instance):
        """
        TODO: add link to optout management here (and an actual feature to support it)
        """
        if instance.sailthru_optout == m.AudienceUser.OPTOUT_NONE:
            css_class = "audb-good"
        else:
            css_class = "audb-bad"

        return mark_safe(
            '<span class="{}">{}</span>'.format(css_class, instance.optout_display_name)
        )

    readonly_sailthru_optout.short_description = "Sailthru optout"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def save_formset(self, request, form, formset, change):
        # this is so that we can add the 'log_override' below
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if isinstance(instance, m.Subscription):
                instance.log_override = {
                    "action": "update",
                    "comment": "{} via Admin by {}".format(
                        "subscribed" if instance.active else "unsubscribed",
                        request.user,
                    ),
                }
            instance.save()
        formset.save_m2m()

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["vars_lookup"] = self._get_vars_lookup()
        return super(AudienceUserAdmin, self).add_view(
            request, form_url, extra_context=extra_context
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["vars_lookup"] = self._get_vars_lookup()
        return super(AudienceUserAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    @staticmethod
    def _get_vars_lookup():
        return json.dumps(
            [{"key": x.key, "type": x.type} for x in m.VarKey.objects.all()]
        )

    @csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        """Mostly copy pasta from super(), but needed to inject a `clean` hook"""

        if not request.POST:
            return super().delete_view(request, object_id, extra_context)

        # ----------------------------------------------------------------------
        #  Start copy pasta (with minor changes)

        opts = self.model._meta

        to_field = request.POST.get(TO_FIELD_VAR)
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )  # why does django prefer this formatting?

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(
                ugettext("%(name)s object with primary key %(key)r does not exist.")
                % {"name": force_text(opts.verbose_name), "key": escape(object_id)}
            )

        using = router.db_for_write(self.model)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        _, _, perms_needed, _ = get_deleted_objects(
            [obj], opts, request.user, self.admin_site, using
        )

        #  End copy pasta
        # ----------------------------------------------------------------------

        if perms_needed:
            raise PermissionDenied

        if obj.email or obj.sailthru_id:
            form = DeleteAudienceUserAdminForm({"id": obj.pk}, instance=obj)
            if not form.is_valid():
                raise PermissionDenied
        return super().delete_view(request, object_id, extra_context)


class EmailChangeAudienceUserAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].help_text = "Enter new email for user."

    def clean_email(self, *args, **kwargs):
        email = self.cleaned_data["email"]
        try:
            email = email.strip()
        except:
            pass
        if not email:
            raise forms.ValidationError("Email can't be blank.")
        if email == self.instance.email:
            raise forms.ValidationError("Email must be different.")
        return email

    def clean(self, *args, **kwargs):
        cleaned = super().clean(*args, **kwargs)
        if "email" not in cleaned:
            return cleaned
        if not settings.SAILTHRU_SYNC_ENABLED:
            return cleaned

        self._obtain_sync_lock()

        new_user = self._meta.model(email=cleaned["email"])
        st_data = self._get_sync_data(self.instance, new_user)
        st_response = self._sync_to_sailthru(st_data)
        if self._re_request_necessary(st_response):
            st_data = self._get_new_user_sync_data(self.instance, cleaned["email"])
            st_response = self._sync_to_sailthru(st_data)
        self._check_response_ok(st_response)
        self._verify_sid(st_response, new_user.sailthru_id)

        self._delete_sync_lock()

        return cleaned

    def save(self, *args, **kwargs):
        if not settings.SAILTHRU_SYNC_ENABLED:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            resp = super().save(*args, **kwargs)
        sync_user_basic.apply_async([self._aud_user.pk])
        return resp

    def _get_sync_data(self, old_user, new_user):
        try:
            sync_logger.debug(
                "Change user (%s) email: converting user data to Sailthru format.",
                str(self.instance.pk),
            )

            converter = sync_converter.EmailChangeAudienceUserToSailthru(
                old_user, new_user
            )
            st_data = converter.convert()
            return st_data
        except ConversionError as e:
            msg = "Problem occured during data conversion for sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(msg)

    def _get_new_user_sync_data(self, user, new_email):
        try:
            sync_logger.debug(
                "Change user (%s) email: converting user data to Sailthru format.",
                str(self.instance.pk),
            )

            old_email = user.email
            user.email = new_email

            converter = sync_converter.AudienceUserToSailthru(user)
            st_data = converter.convert()

            user.email = old_email
            return st_data
        except ConversionError as e:
            msg = "Problem occured during data conversion for sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(msg)

    def _sync_to_sailthru(self, data):
        try:
            sync_logger.debug(
                "Change user (%s) email: Posting data to Sailthru.",
                str(self.instance.pk),
            )

            response = sailthru_client().api_post("user", data)
            return response
        except Exception as e:
            msg = "Problem occured during request to Sailthru. {}.".format(e)
            sentry_sdk.capture_exception(e)
            sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(msg)

    def _re_request_necessary(self, response):
        if response.is_ok():
            return False

        error = response.get_error()
        error_code = error.get_error_code()
        if error_code != SailthruErrors.INVALID_EMAIL:
            return False
        if self.instance.email not in error.get_message():
            return False
        msg = "Sailthru rejected original email. Will attempt to create new user."
        sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))
        return True

    def _check_response_ok(self, response):
        if not response.is_ok():
            msg = "Sailthru rejected request to change email."
            failure = sync_models.SyncFailure.objects.from_sailthru_error_response(
                msg, self.instance, response
            )
            sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(failure.get_admin_anchor())
        try:
            response_data = response.get_body()
            response_data["keys"]["email"]
        except KeyError:
            msg = "Sailthru response missing expected values."
            failure = sync_models.SyncFailure.objects.from_sailthru_response(
                msg, self.instance, response
            )
            sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(failure.get_admin_anchor())

    def _verify_sid(self, response, sid):
        st_sid = response.get_body()["keys"]["sid"]
        if sid and sid != st_sid:
            msg = "Sailthru changed Sailthru ID from {} to {}.".format(sid, st_sid)
            failure = sync_models.SyncFailure.objects.from_sailthru_response(
                msg, self.instance, response
            )
            sync_logger.debug("Change user (%s) email: " + msg, str(self.instance.pk))

            self._delete_sync_lock()
            raise forms.ValidationError(failure.get_admin_anchor())

    def _delete_sync_lock(self):
        with transaction.atomic():
            self._sync_lock.delete()

    def _obtain_sync_lock(self):
        try:
            with transaction.atomic():
                self._aud_user = m.AudienceUser.objects.get(pk=self.instance.pk)
            lock = sync_models.SyncLock(locked_instance=self._aud_user)
            with transaction.atomic():
                lock.save()
        except m.AudienceUser.DoesNotExist:
            raise forms.ValidationError("This user has been deleted.")
        except IntegrityError:
            raise forms.ValidationError(
                "This user is currently locked--preventing syncing with Sailthru."
            )
        self._sync_lock = lock


class EmailChangeAudienceUserAdmin(admin.ModelAdmin):
    form = EmailChangeAudienceUserAdminForm
    fields = ("email",)
    search_fields = ("email",)

    def get_actions(self, *args, **kwargs):
        return []

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class SubscriptionTriggerInline(admin.TabularInline):
    extra = 1
    fk_name = "primary_list"
    model = m.SubscriptionTrigger


class ListAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {"widget": forms.TextInput(attrs={"size": "60"})},
    }

    inlines = (SubscriptionTriggerInline,)

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "type",
                    "sync_externally",
                    "no_unsubscribe",
                    "archived",
                ),
            },
        ),
    )
    change_fieldsets = add_fieldsets + (
        ("Reference", {"fields": ("zephyr_optout_code",)}),
    )

    list_display = [
        "slug_edit",
        "type",
        "sync_externally",
        "archived",
        "no_unsubscribe",
        "stats",
    ]

    list_filter = [
        "type",
        "sync_externally",
        "archived",
        "no_unsubscribe",
    ]

    ordering = [
        "archived",
        "type",
        "slug",
    ]

    search_fields = ("slug",)

    class Media:
        css = {
            "all": ("core/admin/css/list.css",),
        }

        js = (
            "core/admin/js/list.js",
            "core/contrib/clipboard/dist/clipboard.min.js",
        )

    def zephyr_optout_code(self, instance):
        params = "&amp;".join(
            [
                "param=st-{}".format(quote_plus(instance.type)),
                "display_name={}".format(quote_plus(instance.name)),
                "list_name={}".format(quote_plus(instance.sailthru_list_name)),
            ]
        )
        zephyr_code = "{{optout_confirm_url + '&amp;{}'}}".format(params)

        markup = format_html(
            """
              <span class="core-list-zephyr-code">
                  <button
                      class="core-list-zephyr-copy-btn"
                      data-clipboard-text="{zephyr_code}"
                  >
                      <img class="core-list-zephyr-copy-img" src="{static_url}"/>
                      <span class="core-list-zephyr-copy-msg">Copied!</span>
                  </button>
                  {zephyr_code}
              </span>
              <span class="core-list-zephyr-help">
                This is code for a generic optout page. For many lists (e.g.
                govexec newsletters), we have official optout pages that would
                be more appropriate than the one specified here.
              </span>
            """,
            zephyr_code=zephyr_code,
            static_url=static("core/admin/img/clipboard.svg"),
        )
        return markup

    zephyr_optout_code.short_description = "Zephyr optout code"

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.change_fieldsets
        return self.add_fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # seems confusing to allow 'slug' or 'type' to be modifiable after create
            return self.readonly_fields + (
                "type",
                "slug",
                "zephyr_optout_code",
                "no_unsubscribe",
            )
        return self.readonly_fields

    def slug_edit(self, obj):
        return obj.slug

    slug_edit.short_description = "Slug / Edit"

    def get_urls(self):
        urls = super(ListAdmin, self).get_urls()
        analyze_url = [
            url(r"^(?P<pk>\d+)/stats/$", self.admin_site.admin_view(self.stats_view)),
        ]
        return analyze_url + urls

    def stats_view(self, request, pk):
        list_obj = self.get_object(request, pk)
        num_users_inactive = m.AudienceUser.objects.filter(
            subscriptions__list_id=pk, subscriptions__active=False
        ).count()
        num_users_active = m.AudienceUser.objects.filter(
            subscriptions__list_id=pk, subscriptions__active=True
        ).count()
        list_users_total = num_users_inactive + num_users_active

        context = {
            "pk": list_obj.pk,
            "name": list_obj.slug,
            "has_permission": True,
            "list_users_total": list_users_total,
            "list_users_active": num_users_active,
            "list_users_inactive": num_users_inactive,
        }
        return HttpResponse(
            django_render_to_string("admin/stats.html", context, request=request)
        )


class SubscriptionLogListFilter(admin.SimpleListFilter):
    title = "list"
    parameter_name = "list_id"

    def lookups(self, request, model_admin):
        return [(request.GET.get("list_id", None), "Current")]

    def queryset(self, request, queryset):
        return queryset.filter(subscription__list__id=self.value())


class SubscriptionLogTimeFilter(DateFieldListFilter):
    def __init__(self, field, request, params, *args, **kwargs):
        super(SubscriptionLogTimeFilter, self).__init__(
            field, request, params, *args, **kwargs
        )

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()

        self.links = (
            # Last year is default
            # this is handled in the get_queryset function in SubscriptionLogAdmin.
            (("Last Year", {})),
            (
                ("Last 6 Months"),
                {
                    self.lookup_kwarg_since: str(
                        today - datetime.timedelta(days=(30 * 6))
                    ),
                },
            ),
            (
                ("Last Month"),
                {
                    self.lookup_kwarg_since: str(today - datetime.timedelta(days=30)),
                },
            ),
            (
                ("Last 7 days"),
                {
                    self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                },
            ),
            (
                ("Last 24 hours"),
                {
                    self.lookup_kwarg_since: str(today - datetime.timedelta(hours=24)),
                },
            ),
        )


class SubscriptionLogOptoutType(admin.SimpleListFilter):
    title = "Optout Type"
    parameter_name = "optout_type"

    def lookups(self, request, model_admin):
        return [
            ("basic", "Basic Optout"),
            ("all", "All Optout"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                subscription__audience_user__sailthru_optout=self.value()
            )
        else:
            return queryset


class NoCountPaginator(Paginator):
    """
    Paginator that does not count the rows in the table.
    This is used because the count query is taking too long.
    Custom pagination on the page should be added to remove the count and just show
    next and prev buttons. Check the change_list template for this.
    """

    @property
    def count(self):
        return 99999999999


class SubscriptionLogAdmin(admin.ModelAdmin):
    actions = [
        "export_as_csv",
    ]
    paginator = NoCountPaginator
    today = datetime.datetime.now().date()
    last_year = today.replace(year=today.year - 1)

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = self.list_display

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            values = []
            for field in field_names:
                values.append(
                    getattr(obj, field)
                    if hasattr(obj, field)
                    else getattr(self, field)(obj)
                )
            writer.writerow(values)

        return response

    export_as_csv.short_description = "Export Selected as CSV"

    list_display = [
        "list_name",
        "action",
        "email",
        "optout_type",
        "comment",
        "timestamp",
    ]

    list_filter = [
        "action",
        ("timestamp", SubscriptionLogTimeFilter),
        SubscriptionLogOptoutType,
        SubscriptionLogListFilter,
    ]

    list_display_links = None

    def list_name(self, obj):
        return obj.subscription.list.name

    def email(self, obj):
        return obj.subscription.audience_user.email

    def optout_type(self, obj):
        return obj.subscription.audience_user.sailthru_optout

    optout_type.admin_order_field = "subscription__audience_user__sailthru_optout"

    def get_queryset(self, request):
        # Only show data if list is present
        if "list_id" in request.GET:
            return (
                super(SubscriptionLogAdmin, self)
                .get_queryset(request)
                .filter(
                    timestamp__gte=self.last_year,
                )
                .select_related("subscription", "subscription__audience_user")
            )
        else:
            return m.SubscriptionLog.objects.none()

    # To remove the default delete action
    def get_actions(self, request):
        actions = super(SubscriptionLogAdmin, self).get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def changelist_view(self, request, extra_context=None):
        context = {
            "list_id": request.GET.get("list_id", None),
            "date": self.last_year,
            "page": int(request.GET.get("p", 0)),
        }
        return super().changelist_view(request, extra_context=context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # To remove link on home page
    def has_module_permission(self, request):
        return False


class ProductAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.CharField: {"widget": forms.TextInput(attrs={"size": "60"})},
    }

    list_display = [
        "name",
        "slug",
        "type",
        "brand",
    ]

    list_display_external_popup = [
        "get_for_external_popup_name",
        "slug",
        "type",
        "brand",
    ]

    list_filter = ["type", "brand"]

    ordering = [
        "slug",
    ]

    search_fields = ("slug",)

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "type",
                    "brand",
                    "subtypes",
                    "topics",
                ),
            },
        ),
    )
    change_fieldsets = add_fieldsets + (
        (
            "Reference",
            {
                "fields": (
                    "csv_columns_html",
                    "sailthru_vars_html",
                ),
            },
        ),
    )

    class Media:
        css = {
            "all": ("core/admin/css/product.css",),
        }
        js = ("core/admin/js/product.js",)

    def changelist_view(self, request, extra_context=None):
        context = {}
        if self.is_external_popup(request):
            context["external_qs"] = "_popup=external"
        if extra_context is not None:
            context.update(extra_context)
        return super().changelist_view(request, extra_context=context)

    def get_fieldsets(self, request, obj=None):
        if obj:
            return self.change_fieldsets
        return self.add_fieldsets

    def get_list_display(self, request):
        if self.is_external_popup(request):
            return self.list_display_external_popup
        return super().get_list_display(request)

    def get_list_display_links(self, request, list_display):
        if self.is_external_popup(request):
            return None
        return super().get_list_display_links(request, list_display)

    def get_for_external_popup_name(self, obj):
        markup = format_html(
            """
            <button
                class='for-external-popup-core-products-name'
                data-name='{name}'
                data-slug='{slug}'
            >
              {name}
            </button>
        """,
            slug=obj.slug,
            name=obj.name,
        )

        return mark_safe(markup)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # we want 'type' and 'slug' to be fixed after initial creation because
            # we use those values to generate things like Sailthru var keys, and it
            # seems like it'd be really confusing if 'type' and/or 'slug' for a product
            # changed after corresponding Sailthru vars were out there in the wild
            return self.readonly_fields + (
                "type",
                "slug",
                "csv_columns_html",
                "sailthru_vars_html",
            )
        return self.readonly_fields

    def is_external_popup(self, request):
        return (
            request.GET.get("_popup", None) == "external"
            or request.POST.get("_popup", None) == "external"
        )

    def response_add(self, request, obj, post_url_continue=None):
        if self.is_external_popup(request):
            template = "admin/core/product/external_popup_response.html"
            context = {
                "slug": obj.slug,
                "name": obj.name,
            }
            return SimpleTemplateResponse(template, context)
        return super().response_add(request, obj, post_url_continue=post_url_continue)


class VarKeyAdmin(admin.ModelAdmin):
    list_display = [
        "key",
        "type",
        "sync_with_sailthru",
    ]
    list_filter = [
        "type",
        "sync_with_sailthru",
    ]


admin.site.register(m.AudienceUser, AudienceUserAdmin)
admin.site.register(m.EmailChangeAudienceUser, EmailChangeAudienceUserAdmin)
admin.site.register(m.List, ListAdmin)
admin.site.register(m.SubscriptionLog, SubscriptionLogAdmin)
admin.site.register(m.Product, ProductAdmin)
admin.site.register(m.ProductSubtype)
admin.site.register(m.ProductTopic)
admin.site.register(m.VarKey, VarKeyAdmin)
