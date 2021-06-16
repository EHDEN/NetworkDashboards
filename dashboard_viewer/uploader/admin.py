import json

from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core import serializers
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from .actions import custom_delete_selected
from .models import Country, DatabaseType, DataSource, UploadHistory, PendingUpload
from .tasks import delete_datasource

IS_POPUP_VAR = "_popup"


admin.site.register(Country)
admin.site.register(DatabaseType)


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = ("data_source", "upload_date")

    def has_add_permission(self, *_, **__):
        return False


@admin.register(PendingUpload)
class PendingUploadAdmin(admin.ModelAdmin):
    list_display = ("data_source", "upload_date", "status")

    def has_add_permission(self, *_, **__):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "acronym", "database_type", "country")

    actions = [custom_delete_selected]

    def get_actions(self, request):
        """
        Remove the default delete selected action
        """
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        delete_datasource.delay(serializers.serialize("json", [obj]))

    def response_delete(self, request, obj_display, obj_id):
        """
        Based on https://github.com/django/django/blob/2.2.17/django/contrib/admin/options.py#L1411
        The only change was the message returned after deletion since the deletion process is
         sent to a background task
        """
        opts = self.model._meta

        if IS_POPUP_VAR in request.POST:
            popup_response_data = json.dumps(
                {
                    "action": "delete",
                    "value": str(obj_id),
                }
            )
            return TemplateResponse(
                request,
                self.popup_response_template
                or [
                    "admin/%s/%s/popup_response.html"
                    % (opts.app_label, opts.model_name),
                    "admin/%s/popup_response.html" % opts.app_label,
                    "admin/popup_response.html",
                ],
                {
                    "popup_response_data": popup_response_data,
                },
            )

        self.message_user(
            request,
            # ONLY CHANGE vv
            _(
                'The %(name)s "%(obj)s" is being deleted on background. '
                "In a few minutes it will stop appearing on the objects list."
            )
            % {
                "name": opts.verbose_name,
                "obj": obj_display,
            },
            messages.SUCCESS,
        )

        if self.has_change_permission(request, None):
            post_url = reverse(
                "admin:%s_%s_changelist" % (opts.app_label, opts.model_name),
                current_app=self.admin_site.name,
            )
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, post_url
            )
        else:
            post_url = reverse("admin:index", current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url)

    def delete_queryset(self, request, queryset):
        delete_datasource.delay(serializers.serialize("json", list(queryset)))
