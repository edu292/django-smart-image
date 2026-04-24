from typing import Any

from django.forms import FileInput


class PreviewImageInput(FileInput):
    template_name = 'smart_image/preview_image_input.html'

    def __init__(self, attrs=None, placeholder=None):
        self.placeholder = placeholder
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['placeholder'] = self.placeholder
        return context

    def format_value(self, value: Any) -> str | None:
        return value
