from django.apps import AppConfig


class JobhuntConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobhunt"

    def ready(self):
        import jobhunt.signals  # noqa
