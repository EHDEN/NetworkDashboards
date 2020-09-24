from bootstrap_datepicker_plus import DatePickerInput
from django import forms

from .fields import CoordinatesField
from .models import DataSource, DatabaseType
from .widgets import ListTextWidget


class SourceForm(forms.ModelForm):
    database_type = forms.CharField(
        max_length=40,
        widget=ListTextWidget(DatabaseType.objects),
        help_text="Type of the data source. You can create a new type.",
    )
    coordinates = CoordinatesField(
        help_text="Coordinates for the location of the data source"
    )

    class Meta:
        model = DataSource
        exclude = ("latitude", "longitude")
        widgets = {
            "release_date": DatePickerInput(),  # format %m/%d/%Y. Using a ModelForm this can't be changed
        }

    def clean_database_type(self):
        return self.cleaned_data["database_type"].title()


class AchillesResultsForm(forms.Form):
    achilles_results_file = forms.FileField()
