from django.apps import AppConfig


class SailthruSyncConfig(AppConfig):
    name = 'sailthru_sync'
    verbose_name = "Sailthru sync"

    def ready(self):
        from . import tasks
        from django.conf import settings

        if settings.SAILTHRU_SYNC_ENABLED and settings.SAILTHRU_SYNC_SIGNALS_ENABLED:
            from .signals.receivers import core_audienceuser
            from .signals.receivers import core_productaction
            from .signals.receivers import core_productactiondetail
            from .signals.receivers import core_subscription
            from .signals.receivers import core_usersource
            from .signals.receivers import core_producttopic
