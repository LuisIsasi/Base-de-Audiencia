from datetime import datetime

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django_extensions.db.models import TimeStampedModel

from .errors import SailthruErrors
from .managers import SyncLockManager
from .querysets import SyncFailureQuerySet


class SyncModel(TimeStampedModel):
    class Meta:
        abstract = True

    def get_admin_url(self, full_url=False):
        reverse_template = "admin:{app_label}_{model_name}_change"
        context = {
            "app_label": self.__class__._meta.app_label.lower(),
            "model_name": self.__class__.__name__.lower(),
        }
        reverse_url = reverse_template.format(**context)
        url = reverse(reverse_url, args=(self.pk,))
        if full_url:
            url = settings.BASE_URL + url
        return url

    def get_admin_anchor_custom(self, msg, full_url=False):
        template = "<a href='{}'>{}</a>"
        url = self.get_admin_url(full_url)
        return mark_safe(template.format(url, msg))

    def get_admin_anchor(self):
        return self.get_admin_anchor_custom(str(self))


class SyncFailure(SyncModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    failed_instance = GenericForeignKey()
    message = models.TextField()
    sailthru_body = JSONField(default=dict, blank=True, null=True)
    sailthru_error_code = models.CharField(max_length=5, null=True, blank=True)
    sailthru_error_message = models.TextField(null=True, blank=True)
    sailthru_error_description = models.TextField(null=True, blank=True)
    sailthru_error_status_code = models.IntegerField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    acknowledged = models.BooleanField(default=False)

    objects = SyncFailureQuerySet.as_manager()

    def __str__(self):
        return self.message


class SyncFailureNotificationGroup(TimeStampedModel):
    INTERESTED_ERRORS = tuple(
        (str(error_code), msg["short-msg"])
        for error_code, msg in SailthruErrors.MESSAGES.items()
    )

    interested_errors = ArrayField(
        models.CharField(
            max_length=5,
        ),
        default=[],
        blank=True,
        null=True,
    )
    interested_group = models.ForeignKey("auth.Group", on_delete=models.CASCADE)
    notification_task = models.ForeignKey(
        "djcelery.PeriodicTask", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return "{}-{}".format(self.interested_group, self.notification_task)


class SyncLock(SyncModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    locked_instance = GenericForeignKey()

    objects = SyncLockManager()

    class Meta:
        unique_together = ("content_type", "object_id")

    @property
    def age(self):
        return datetime.now() - self.timestamp

    def __str__(self):
        return str(self.locked_instance)
