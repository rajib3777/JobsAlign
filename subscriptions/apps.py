from django.apps import AppConfig

class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'

    def ready(self):
        # register signals for payments.Transaction integration
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass

