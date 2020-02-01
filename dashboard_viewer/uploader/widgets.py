from django import forms
from django.forms import widgets
from django.template import loader
from django.utils.safestring import mark_safe


class ListTextWidget(forms.TextInput):
    """
    text input with autocomplete with already existing values
     for a specific field
    """

    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list': 'list__%s' % self._name})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return text_html + data_list


class CoordinatesWidget(widgets.TextInput):
    map_width = 600
    map_height = 400
    display_raw = False

    class Media:
        css = ("leaflet/dist/leaflet.css",)
        js = ("leaflet/dist/leaflet.js",)

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        text_input = super(CoordinatesWidget, self).render(name, value, attrs, renderer)

        return loader.render_to_string(
            "coordinates_widget.html",
            {
                "name": name,
                "text_input": mark_safe(text_input),
                "text_input_id": attrs["id"]
            }
        )


