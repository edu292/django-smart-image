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


class CamImageInput(FileInput):
    template_name = 'smart_image/cam_image_input.html'

    def __init__(self, capture_width=1920, capture_height=1080, attrs=None):
        self.capture_width = capture_width
        self.capture_height = capture_height
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['capture_width'] = self.capture_width
        context['widget']['capture_height'] = self.capture_height

        return context

    def format_value(self, value):
        return value
