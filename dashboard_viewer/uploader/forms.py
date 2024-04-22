import constance
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
        fields = ("name", "acronym", "country", "link", "database_type", "hash")
        widgets = {
            "database_type": ListTextWidget(DatabaseType.objects),
            "release_date": DatePickerInput(),  # format %m/%d/%Y. Using a ModelForm this can't be changed
            "hash": forms.HiddenInput(),
        }

    def clean_database_type(self):
        return self.cleaned_data["database_type"].strip().title()


class EditSourceForm(SourceForm):
    class Meta(SourceForm.Meta):
        fields = ("name", "country", "link", "database_type") + (
            ("draft",) if constance.config.UPLOADER_ALLOW_EDIT_DRAFT_STATUS else ()
        )


class AchillesResultsForm(forms.Form):
    if constance.config.ALLOW_ONBOARDING_UPLOAD:
        results_file = forms.FileField(required=False, label='Catalogue Export File')
    else:
        results_file = forms.FileField()

class OnboardingReportForm(forms.Form):
    onboarding_results_file = forms.FileField(required=False, label='Onboarding Report file (Optional)')