from django.db import transaction
from django.db.models import FileField


def delete_on_model_delete(sender, instance, **kwargs):
    for field in instance._meta.fields:
        if isinstance(field, FileField):
            file = getattr(instance, field.name)
            if file and file.storage.exists(file.name):
                transaction.on_commit(lambda f=file: f.delete(save=False))

def delete_old_file(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field in instance._meta.fields:
        if isinstance(field, FileField):
            old_file = getattr(old_instance, field.name)
            new_file = getattr(instance, field.name)

            if old_file and old_file != new_file and old_file.storage.exists(old_file.name):
                transaction.on_commit(lambda f=old_file: f.delete(save=False))
