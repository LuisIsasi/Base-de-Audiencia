from django import template

from .. import models as m


register = template.Library()


@register.inclusion_tag('sailthru_sync/admin_notifications.html', takes_context=True)
def show_sync_failure_notifications(context):
    request = context['request']
    notification_groups = (
        m.SyncFailureNotificationGroup.objects
        .filter(interested_group__in=request.user.groups.all())
    )
    if not notification_groups:
        return {}

    errors = {
        error
        for group in notification_groups
        for error in group.interested_errors
    }

    has_failures = (
        m.SyncFailure.objects
        .filter(
            sailthru_error_code__in=errors,
            resolved=False,
        )
        .exists()
    )

    template_context = {
        'sync_failure_notifications': {
            'exists': has_failures,
        },
    }

    return template_context
