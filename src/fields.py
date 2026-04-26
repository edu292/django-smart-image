import io
import math
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import ImageField
from django.utils.translation import gettext_lazy as _
from PIL import Image


def is_float(str: Any):
    try:
        float(str)
    except TypeError:
        return False

    return True


class WebPImageField(ImageField):
    def __init__(self, quality: int = 80, *args: Any, **kwargs: Any) -> None:
        if not is_float(quality):
            raise TypeError(f'Expect quality to be a valid float. Given {quality}')
        super().__init__(*args, **kwargs)
        self.quality = quality

    def deconstruct(self) -> Any:
        name, path, args, kwargs = super().deconstruct()
        kwargs['quality'] = self.quality

        return name, path, args, kwargs

    def process_image(self, img):
        return img

    def get_prep_value(self, value):
        prepped_value = super().get_prep_value(value)

        if prepped_value == '':
            return None

        return prepped_value

    def pre_save(self, model_instance, add):
        file = getattr(model_instance, self.attname)

        if file and not file._committed:
            img = Image.open(file)

            if img.format != 'WEBP':
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                img = self.process_image(img)

                output = io.BytesIO()
                img.save(output, format='WEBP', quality=self.quality)
                output.seek(0)

                file.file = ContentFile(output.read())
                file.name = Path(file.name).with_suffix('.webp')

        return super().pre_save(model_instance, add)


class ImageDimensionMixin:
    def __init__(
        self,
        width: int | None = None,
        height: int | None = None,
        aspect_ratio: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if aspect_ratio and (width or height):
            raise TypeError('Provide EITHER width and height OR aspect_ratio, not both.')

        invalid_aspect_ratio_error = TypeError(
            f'Aspect ratio must be "width/height" (e.g., "1/1" or "16/9"). Current: {aspect_ratio}'
        )
        if aspect_ratio:
            parts = aspect_ratio.split('/', 1)
            if len(parts) != 2 or any(not is_float(p) for p in parts):
                raise invalid_aspect_ratio_error

        self.width = width
        self.height = height
        self.aspect_ratio = aspect_ratio

        super().__init__(*args, **kwargs)

    def deconstruct(self) -> Any:
        name, path, args, kwargs = super().deconstruct()

        if self.width:
            kwargs['width'] = self.width
        if self.height:
            kwargs['height'] = self.height
        if self.aspect_ratio:
            kwargs['aspect_ratio'] = self.aspect_ratio

        return name, path, args, kwargs


class WebPValidatedImageField(ImageDimensionMixin, WebPImageField):
    def formfield(self, **kwargs):
        defaults = {'validators': [self.validate_dimensions]}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def validate_dimensions(self, image):
        if not image:
            return

        img = Image.open(image)
        image_width, image_height = img.size

        if self.width and image_width != self.width:
            raise ValidationError(_(f'Width must be {self.width}px (given: {image_width}px).'))
        if self.height and image_height != self.height:
            raise ValidationError(_(f'Height must be {self.height}px (given: {image_height}px).'))

        if self.aspect_ratio:
            target_width_aspect, target_height_aspect = (float(ratio) for ratio in self.aspect_ratio.split('/'))
            target_ratio = target_width_aspect / target_height_aspect
            image_ratio = image_width / image_height
            if not math.isclose(target_ratio, image_ratio):
                divisor = math.gcd(image_width, image_height)
                image_width_aspect = image_width / divisor
                image_height_aspect = image_height / divisor
                raise ValidationError(
                    _(
                        f'The image must be in the {target_width_aspect}/{target_height_aspect} aspect ratio (given: {image_width_aspect}/{image_height_aspect})'
                    )
                )


class WebPAutoCropField(ImageDimensionMixin, WebPImageField):
    def process_image(self, img: Image.Image) -> Image.Image:
        if self.aspect_ratio:
            target_w_aspect, target_h_aspect = (float(aspect) for aspect in self.aspect_ratio.split('/'))
            target_ratio = target_w_aspect / target_h_aspect
        elif self.width and self.height:
            target_ratio = self.width / self.height

        original_w, original_h = img.size
        current_ratio = original_w / original_h

        if not math.isclose(current_ratio, target_ratio):
            if current_ratio > target_ratio:
                new_w = int(original_h * target_ratio)
                offset = (original_w - new_w) // 2
                img = img.crop((offset, 0, offset + new_w, original_h))
            else:
                new_h = int(original_w / target_ratio)
                offset = (original_h - new_h) // 2
                img = img.crop((0, offset, original_w, offset + new_h))

        if self.width and self.height and img.width > self.width:
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)

        return img
