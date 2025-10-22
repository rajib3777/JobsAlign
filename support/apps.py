from django.apps import AppConfig

class SupportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'support'

    def ready(self):
        try:
            from . import signals  
        except Exception:
            pass

