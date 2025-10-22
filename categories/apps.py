from django.apps import AppConfig

class CategoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'categories'

    def ready(self):
        # import signals
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
