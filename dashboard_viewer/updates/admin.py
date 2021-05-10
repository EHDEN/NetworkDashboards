from django import forms
from django.contrib import admin

from . import models


@admin.register(models.RequestsGroupLog)
class RequestGroupLogAdmin(admin.ModelAdmin):
    list_display = ("group", "trigger_upload", "success_count", "time")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(models.RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ("group", "request", "success")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(models.RequestsGroup)


class RequestAdminForm(forms.ModelForm):
    class Meta:
        model = models.Request
        fields = "__all__"


@admin.register(models.Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ("group", "order")
    form = RequestAdminForm
