
from bootstrap_datepicker_plus import DatePickerInput
from django import forms

from .fields import CoordinatesField
from .models import DataSource, DatabaseType, Country
from .widgets import ListTextWidget

VERSION_REGEX = r'[\d.]*\d+'


class SourceForm(forms.ModelForm):
    database_type = forms.CharField(
        max_length = 40,
        widget = ListTextWidget(DatabaseType.objects),
        help_text = "Type of the data source. You can create a new type.",
    )
    coordinates = CoordinatesField(
        help_text = "Coordinates for the location of the data source"
    )

    class Meta:
        model = DataSource
        exclude = (
            "latitude",
            "longitude"
        )
        widgets = {
            'release_date': DatePickerInput(),
        }

    def clean_database_type(self):
        return self.cleaned_data["database_type"].title()


class AchillesResultsForm(forms.Form):
    achilles_version = forms.RegexField(VERSION_REGEX)
    achilles_generation_date = forms.DateField(widget=DatePickerInput)
    cdm_version = forms.RegexField(VERSION_REGEX)
    vocabulary_version = forms.RegexField(VERSION_REGEX)
    achilles_results = forms.FileField()
    has_header = forms.BooleanField(
        help_text="Does the achilles results file has a header line",
        initial=True,
        required=False
    )
