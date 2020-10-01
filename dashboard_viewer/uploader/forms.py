from bootstrap_datepicker_plus import DatePickerInput
from django import forms

from .fields import CoordinatesField
from .models import DatabaseType, DataSource
from .widgets import ListTextWidget


class SourceForm(forms.ModelForm):
    coordinates = CoordinatesField(
        help_text="Coordinates for the location of the data source"
    )

    class Meta:
        model = DataSource
        fields = ("name", "acronym", "release_date", "country", "link", "database_type")
        widgets = {
            "database_type": ListTextWidget(DatabaseType.objects),
            "release_date": DatePickerInput(),  # format %m/%d/%Y. Using a ModelForm this can't be changed
        }

    def clean_database_type(self):
        return self.cleaned_data["database_type"].trim().title()


class AchillesResultsForm(forms.Form):
    achilles_results_file = forms.FileField()
