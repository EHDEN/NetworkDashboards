from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _, gettext_lazy


def custom_delete_selected(modeladmin, request, queryset):
    """
    Based on https://github.com/django/django/blob/2.2.17/django/contrib/admin/actions.py#L13
    The only change was the message returned after deletion since the deletion process is
     sent to a background task
    """
    opts = modeladmin.model._meta

    deletable_objects, model_count, perms_needed, protected = modeladmin.get_deleted_objects(queryset, request)

    if request.POST.get("post") and not protected:
        if perms_needed:
            raise PermissionDenied
        n = queryset.count()
        if n:
            for obj in queryset:
                obj_display = str(obj)
                modeladmin.log_deletion(request, obj, obj_display)
            modeladmin.delete_queryset(request, queryset)
            # ONLY CHANGE vv
            modeladmin.message_user(
                request,
                _(
                    "Deleting %(count)d %(items)s on background. "
                    "In a few minutes they will stop showing on the objects list."
                ) % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                },
                messages.SUCCESS
            )
        # Return None to display the change list page again.
        return None

    objects_name = model_ngettext(queryset)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Are you sure?")

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": title,
        "objects_name": str(objects_name),
        "deletable_objects": [deletable_objects],
        "model_count": dict(model_count).items(),
        "queryset": queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "media": modeladmin.media,
    }

    request.current_app = modeladmin.admin_site.name

    # Display the confirmation page
    return TemplateResponse(
        request,
        "admin/datasource/delete_selected_confirmation.html",
        context
    )


custom_delete_selected.allowed_permissions = ('delete',)
custom_delete_selected.short_description = gettext_lazy("Delete selected %(verbose_name_plural)s")
