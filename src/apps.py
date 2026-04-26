from django.apps import AppConfig
from django.db.models import FileField


class SmartImageConfig(AppConfig):
    name = 'smart_image'

    def ready(self) -> None:
        from django.apps import apps

        for model in apps.get_models():
            has_file_field = any(isinstance(field, FileField) for field in model._meta.fields)
            if has_file_field:
                self.connect_signal(model)

    def connect_signal(self, model):
        from django.db.models.signals import post_delete, pre_save

        from .handlers import delete_old_file, delete_on_model_delete

        post_delete.connect(delete_on_model_delete, sender=model, dispatch_uid=f'{model._meta.label}_cleanup_delete')
        pre_save.connect(delete_old_file, sender=model, dispatch_uid=f'{model._meta.label}_cleanup_change')
