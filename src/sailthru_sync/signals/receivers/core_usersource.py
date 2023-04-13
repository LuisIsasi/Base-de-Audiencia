from core import models as core_models
from django.db.models.signals import post_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from ...tasks import sync_user_basic


@receiver(post_save, sender=core_models.UserSource, dispatch_uid='sailthru_sync::signals::source_post_save')
def source_post_save(sender, **kwargs):
    instance = kwargs['instance']
    if instance.audience_user.email:
        on_commit(lambda: sync_user_basic.apply_async([instance.audience_user.pk]))
