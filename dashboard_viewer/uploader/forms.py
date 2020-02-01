
from django import forms

from .models import Sources
from .widgets import ListTextWidget, CoordinatesWidget

from bootstrap_datepicker_plus import DatePickerInput

VERSION_REGEX = r'[0-9]+\.[0-9]+\.[0-9]+'


class SourceFrom(forms.ModelForm):
    coordinates = forms.CharField(max_length=40, widget=CoordinatesWidget)

    class Meta:
        model = Sources
        fields = (
            'name',
            'release_date',
            'database_type',
            'location',
            'link',
        )
        widgets = {
            'release_date': DatePickerInput(),
        }

    def save(self, commit=True):
        pass

    def clean_database_type(self):
        return self.cleaned_data["database_type"].title()

    def __init__(self, database_types, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['database_type'].widget = ListTextWidget(database_types, 'database-types-list')


class AchillesResultsForm(forms.Form):
    achilles_version = forms.RegexField(VERSION_REGEX)
    achilles_generation_date = forms.DateField(widget=DatePickerInput)
    cdm_version = forms.RegexField(VERSION_REGEX)
    vocabulary_version = forms.RegexField(VERSION_REGEX)
    achilles_results = forms.FileField()
