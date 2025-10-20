from django.apps import AppConfig

class ChatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chats'

    def ready(self):
        # import signals to ensure receivers registered
        from . import signals  # noqa: F401

