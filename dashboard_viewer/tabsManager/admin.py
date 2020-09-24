from django import forms
from django.contrib import admin

from .models import Logo, Tab, TabGroup


class LogoForm(forms.ModelForm):
    class Meta:
        model = Logo
        fields = "__all__"

    def clean(self):
        image = self.cleaned_data.get("image")
        url = self.cleaned_data.get("url")

        if not image and not url:
            raise forms.ValidationError("Must define the image or url field")
        if image and url:
            raise forms.ValidationError("Define only the image or url field")

        return self.cleaned_data


class LogoAdmin(admin.ModelAdmin):
    form = LogoForm


admin.site.register(Logo, LogoAdmin)
admin.site.register(Tab)
admin.site.register(TabGroup)
