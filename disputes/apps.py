from django.apps import AppConfig

class DisputesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'disputes'

    def ready(self):
       
        try:
            from . import signals  
        except Exception:
            pass

