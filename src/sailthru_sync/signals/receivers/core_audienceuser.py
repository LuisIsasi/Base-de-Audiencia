from core import models as core_models
from django.db.models.signals import post_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from ...tasks import sync_user_basic


@receiver(post_save, sender=core_models.AudienceUser, dispatch_uid='sailthru_sync::signals::audienceuser_post_save')
def user_post_save(sender, **kwargs):
    instance = kwargs['instance']

    if getattr(instance, '_sync_disabled', False):
        return

    if not instance.email:
        return
    on_commit(lambda: sync_user_basic.apply_async([instance.pk]))
