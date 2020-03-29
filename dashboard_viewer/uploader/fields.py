
from django.forms import fields

from .widgets import CoordinatesWidget


class CoordinatesField(fields.MultiValueField):
    widget = CoordinatesWidget()

    def __init__(self, *args, **kwargs):
        _fields = (
            fields.CharField(max_length=45),
            fields.CharField(max_length=45),
        )

        super().__init__(_fields, *args, **kwargs)

    def compress(self, data_list):
        return ','.join(data_list)
