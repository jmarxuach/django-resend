from django.apps import AppConfig


class DjangoResendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_resend'
    verbose_name = 'Django Resend'

    def ready(self):
        import django_resend.signals  # noqa
