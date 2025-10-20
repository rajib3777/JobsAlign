from django.apps import AppConfig

class RecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommendations'

    def ready(self):
        # register signals if any
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
