
from bootstrap_datepicker_plus import DatePickerInput
from django import forms

from .fields import CoordinatesField
from .models import DataSource, DatabaseType
from .widgets import ListTextWidget

VERSION_REGEX = r'[0-9]+\.[0-9]+\.[0-9]+'


class SourceFrom(forms.ModelForm):
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
        exclude = (
            "latitude",
            "longitude",
        )
        widgets = {
            'release_date': DatePickerInput(),
        }

    def clean_database_type(self):
        db_type_title = self.cleaned_data["database_type"].title()
        try:
            db_type = DatabaseType.objects.get(type=db_type_title)
        except DatabaseType.DoesNotExist:
            db_type = None

        if db_type is not None:
            return db_type
        else:
            db_type = DatabaseType(type=db_type_title)
            db_type.save()
            return db_type


class AchillesResultsForm(forms.Form):
    achilles_version = forms.RegexField(VERSION_REGEX)
    achilles_generation_date = forms.DateField(widget=DatePickerInput)
    cdm_version = forms.RegexField(VERSION_REGEX)
    vocabulary_version = forms.RegexField(VERSION_REGEX)
    achilles_results = forms.FileField()
