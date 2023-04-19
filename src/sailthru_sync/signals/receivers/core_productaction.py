from core import models as core_models
from django.db.models.signals import post_save
from django.db.transaction import on_commit
from django.dispatch import receiver

from ...tasks import sync_user_basic


@receiver(
    post_save,
    sender=core_models.ProductAction,
    dispatch_uid="sailthru_sync::signals::product_action_post_save",
)
def product_action_post_save(sender, **kwargs):
    instance = kwargs["instance"]
    au = instance.audience_user
    if au.email:
        on_commit(lambda: sync_user_basic.apply_async([au.pk]))
