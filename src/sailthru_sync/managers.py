from django.contrib.contenttypes.models import ContentType
from django.db import models


class SyncLockManager(models.Manager):
    def get_from_locked_instance(self, locked_instance):
        obj = self.get(
            object_id=locked_instance.pk,
            content_type=ContentType.objects.get_for_model(locked_instance),
        )
        return obj
