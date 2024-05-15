from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dg_app'
    
    def ready(self):
        from .models import delete_file_from_azure
