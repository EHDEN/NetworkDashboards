from django import forms
from django.forms import widgets
from django.template import loader
from django.utils.safestring import mark_safe
import re


class ListTextWidget(forms.TextInput):
    """
    text input with autocomplete with already existing values
     for a specific field
    """

    def __init__(self, query_obj, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self.query_obj = query_obj

    def render(self, name, value, attrs=None, renderer=None):
        attrs.update({"list": f"{name}_list"})
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = f'<datalist id="{name}_list">'
        for item in self.query_obj.all():
            data_list += f'<option value="{item}">'
        data_list += "</datalist>"

        return text_html + data_list


class CoordinatesWidget(widgets.MultiWidget):
    html_tags_regex = re.compile("(<[^>]*>)")

    class Media:
        css = {
            "all": (
                "leaflet/dist/leaflet.css",
                "css/coordinates_widget.css",
            ),
        }
        js = ("leaflet/dist/leaflet.js", "js/coordinates_map.js")

    def __init__(self, map_height=500, *args, **kwargs):
        self.map_height = map_height

        widgets = [
            forms.TextInput(
                attrs={
                    "readonly": True,
                    "placeholder": "Latitude",
                }
            ),
            forms.TextInput(
                attrs={
                    "readonly": True,
                    "placeholder": "Longitude",
                }
            ),
        ]

        super().__init__(widgets, *args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        text_inputs = super(CoordinatesWidget, self).render(
            name, value, attrs, renderer
        )

        lat_input, lon_input = [
            inp for inp in self.html_tags_regex.split(text_inputs) if inp != ""
        ]

        return loader.render_to_string(
            "coordinates_widget.html",
            {
                "name": name,
                "lat_input": mark_safe(lat_input),
                "lon_input": mark_safe(lon_input),
                "map_height": self.map_height,
            },
        )

    def decompress(self, value):
        if value:
            return value.split(",")
        return [None, None]
