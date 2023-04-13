from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Audience Data'

    def ready(self):
        from .signals import receivers
