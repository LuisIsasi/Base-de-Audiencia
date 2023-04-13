from core import models as core_models
from django.db.models.signals import post_save, pre_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from ...tasks import sync_user_basic


@receiver(pre_save, sender=core_models.Subscription, dispatch_uid='sailthru_sync::signals::subscription_pre_save')
def subscription_pre_save(sender, **kwargs):
    instance = kwargs['instance']
    if not instance.pk:
        instance._sailthru_sync_can_sync = (
            instance.list.can_sync() and
            instance.audience_user.email and
            instance.active
        )
    else:
        instance._sailthru_sync_can_sync = (
            instance.list.can_sync() and
            instance.audience_user.email and
            (
                instance.active or
                instance.active != type(instance).objects.get(pk=instance.pk).active
            )
        )


@receiver(post_save, sender=core_models.Subscription, dispatch_uid='sailthru_sync::signals::subscription_post_save')
def subscription_post_save(sender, **kwargs):
    instance = kwargs['instance']
    if not instance._sailthru_sync_can_sync:
        return
    on_commit(lambda: sync_user_basic.apply_async([instance.audience_user.pk]))
