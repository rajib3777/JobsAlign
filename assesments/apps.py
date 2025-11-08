from django.apps import AppConfig


class AssesmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assesments'

    def ready(self):
        import assesments.signals  # noqa

