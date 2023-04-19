# from core import models as core_models
# from django.db.models import Q
# from django.db.models.signals import post_save, pre_save
# from django.db.transaction import on_commit
# from django.dispatch import receiver
#
# from ...tasks import sync_user_basic
#
#
# @receiver(pre_save, sender=core_models.List, dispatch_uid='sailthru_sync::signals::list_pre_save')
# def list_pre_save(sender, **kwargs):
#    instance = kwargs['instance']
#    instance._sailthru_sync_can_sync = False
#    if not instance.pk:
#        return
#    instance._sailthru_sync_can_sync = (
#        instance.can_sync() or
#        (instance.can_sync() != type(instance).objects.get(pk=instance.pk).can_sync())
#    )
#
#
# @receiver(post_save, sender=core_models.List, dispatch_uid='sailthru_sync::signals::list_post_save')
# def list_post_save(sender, **kwargs):
#    instance = kwargs['instance']
#    if not instance._sailthru_sync_can_sync:
#        return
#    aud_users = set(
#        instance.subscriptions
#        .filter(active=True)
#        .exclude(
#            Q(audience_user__email="") |
#            Q(audience_user__email__isnull=True)
#        )
#        .values_list("audience_user_id", flat=True)
#    )
#    on_commit(
#        lambda: [
#            sync_user_basic.apply_async([au])
#            for au in aud_users
#        ]
#    )
