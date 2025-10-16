from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # import signals to ensure automatic creation hooks run
        try:
            import accounts.signals  # noqa
        except Exception:
            # log or ignore in early migrations
            pass

