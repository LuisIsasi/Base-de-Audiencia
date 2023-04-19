from core import models as core_models
from django.db.models import Q
from django.db.models.signals import m2m_changed
from django.db.transaction import on_commit
from django.dispatch import receiver

from ...tasks import sync_user_basic


@receiver(
    m2m_changed,
    sender=core_models.Product.topics.through,
    dispatch_uid="sailthru_sync::signals::producttopic_m2m_changed",
)
def producttopic_m2m_changed(sender, **kwargs):
    instance = kwargs["instance"]
    action = kwargs["action"]
    reverse = kwargs["reverse"]

    valid_actions = ["post_add", "post_remove", "post_clear"]
    if action in valid_actions:
        if reverse:
            product_actions = core_models.ProductAction.objects.filter(
                product__in=instance.product_set.all()
            )
        else:
            product_actions = core_models.ProductAction.objects.filter(product=instance)

        aud_users = set(
            product_actions.exclude(
                Q(audience_user__email="") | Q(audience_user__email__isnull=True)
            ).values_list("audience_user_id", flat=True)
        )

        on_commit(lambda: [sync_user_basic.apply_async([au]) for au in aud_users])
