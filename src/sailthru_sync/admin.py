import json
from django import forms
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.utils.safestring import mark_safe

from . import models as m


class SyncFailureAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'message',
        'get_failed_instance',
        'resolved',
        'created',
    )

    exclude = (
        'sailthru_body',
        'content_type',
        'object_id',
        'acknowledged',
    )
    readonly_fields = (
        'get_failed_instance',
        'message',
        'sailthru_error_message',
        'sailthru_error_code',
        'sailthru_error_description',
        'sailthru_error_status_code',
        'get_sailthru_body',
        'created',
        'modified',
    )

    list_filter = (
        'resolved',
    )

    fieldsets = (
        (None, {
            'fields': (
                'get_failed_instance',
                'message',
                'created',
                'modified',
            ),
        }),
        ('Sailthru Data', {
            'fields': (
                'sailthru_error_message',
                'sailthru_error_code',
                'sailthru_error_description',
                'sailthru_error_status_code',
                'get_sailthru_body',
            ),
        }),
        ('Status', {
            'fields': (
                'resolved',
            ),
        }),
    )

    actions = [
        'resolve_sync_failures',
    ]

    def get_failed_instance(self, obj):
        if obj.pk and obj.failed_instance:
            template = "<a href='{url}'>{text}</a>"
            reverse_template = "admin:{app_label}_{model_name}_change"

            reverse_url = reverse_template.format(
                app_label=obj.content_type.app_label,
                model_name=obj.content_type.model,
            )
            url = reverse(reverse_url, args=(obj.failed_instance.pk,))

            return mark_safe(template.format(url=url, text=str(obj.failed_instance)))
        return ""
    get_failed_instance.short_description = "Failed Instance"

    def get_sailthru_body(self, obj):
        if not obj.sailthru_body:
            return ""
        pre = "<p><pre>\n{}\n</pre></p>"
        pretty = json.dumps(obj.sailthru_body, indent=2, sort_keys=True)
        return mark_safe(pre.format(pretty))
    get_sailthru_body.short_description = "Sailthru body"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def resolve_sync_failures(self, request, queryset):
        queryset.update(resolved=True)


class SyncLockAdmin(admin.ModelAdmin):
    list_display = (
        'locked_instance',
    )
    exclude = (
        'content_type',
        'object_id',
    )
    readonly_fields = (
        'locked_instance',
    )

    def has_add_permission(self, *args, **kwargs):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save'] = False
        extra_context['show_save_as_new'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        return super().change_view(request, object_id, form_url, extra_context)


class SyncFailureNotificationGroupAdminForm(forms.ModelForm):
    interested_errors = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={
            'size': '10',
            'style': 'height: auto;',
        }),
        choices=sorted(
            m.SyncFailureNotificationGroup.INTERESTED_ERRORS,
            key=lambda x: x[1],
        ),
        required=False,
    )


class SyncFailureNotificationGroupAdmin(admin.ModelAdmin):
    form = SyncFailureNotificationGroupAdminForm

    fields = (
        'interested_group',
        'notification_task',
        'interested_errors',
    )

    list_display = (
        'pk',
        'interested_group',
        'notification_task',
    )


admin.site.register(m.SyncFailure, SyncFailureAdmin)
admin.site.register(m.SyncFailureNotificationGroup, SyncFailureNotificationGroupAdmin)
admin.site.register(m.SyncLock, SyncLockAdmin)
