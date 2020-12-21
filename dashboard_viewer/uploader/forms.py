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
        fields = ("name", "acronym", "country", "link", "database_type")
        widgets = {
            "database_type": ListTextWidget(DatabaseType.objects),
        }

    def clean_database_type(self):
        return self.cleaned_data["database_type"].strip().title()


class AchillesResultsForm(forms.Form):
    results_files = forms.FileField()
