from django.contrib import messages
from django.core import serializers
from django.utils.translation import gettext as _, gettext_lazy

from .tasks import refresh_materialized_views_task


def refresh_materialized_views_action(model_admin, request, queryset):
    refresh_materialized_views_task.delay(serializers.serialize("json", queryset))

    model_admin.message_user(
        request,
        _("Refreshing materialized view(s) on a background task."),
        messages.SUCCESS,
    )


refresh_materialized_views_action.short_description = gettext_lazy(
    "Refresh selected %(verbose_name_plural)s"
)
