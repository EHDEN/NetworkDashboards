from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import flatten_fieldsets, quote, unquote
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.forms import all_valid
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.translation import gettext as _
from django_celery_results.models import TaskResult

from .models import MaterializedQuery
from .tasks import create_materialized_view


@admin.register(MaterializedQuery)
class MaterializedQueryAdmin(admin.ModelAdmin):
    save_as_continue = False
    save_as = False

    list_display = (
        "name",
        "dashboards",
    )

    def _changeform_view(self, request, object_id, form_url, extra_context):  # noqa
        # Copied from django.contrib.admin.options.py
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(
                "The field %s cannot be referenced." % to_field
            )

        opts = self.model._meta

        if request.method == "POST" and "_saveasnew" in request.POST:
            object_id = None

        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            if request.method == "POST":
                if not self.has_change_permission(request, obj):
                    raise PermissionDenied
            else:
                if not self.has_view_or_change_permission(request, obj):
                    raise PermissionDenied

            if obj is None:
                return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        ModelForm = self.get_form(request, obj, change=not add)
        if request.method == "POST":
            old_values = None
            if obj is not None:
                old_values = {
                    "name": obj.name,
                    "query": obj.query,
                }
            form = ModelForm(request.POST, request.FILES, instance=obj)
            form_validated = form.is_valid()
            if form_validated:
                new_object = self.save_form(request, form, change=not add)
            else:
                new_object = form.instance
            formsets, inline_instances = self._create_formsets(
                request, new_object, change=not add
            )
            if all_valid(formsets) and form_validated:
                self.background_task = create_materialized_view.delay(
                    request.user.pk,
                    old_values,
                    serializers.serialize("json", [new_object]),
                    self.construct_change_message(request, form, formsets, add),
                )
                if add:
                    return self.response_add(request, new_object)
                return self.response_change(request, new_object)
        else:
            if add:
                form = ModelForm(initial=self.get_changeform_initial_data(request))
                formsets, inline_instances = self._create_formsets(
                    request, form.instance, change=False
                )
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(
                    request, obj, change=True
                )

        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            self.get_prepopulated_fields(request, obj)
            if add or self.has_change_permission(request, obj)
            else {},
            readonly_fields,
            model_admin=self,
        )
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(
            request, formsets, inline_instances, obj
        )
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        if add:
            title = _("Add %s")
        elif self.has_change_permission(request, obj):
            title = _("Change %s")
        else:
            title = _("View %s")
        context = {
            **self.admin_site.each_context(request),
            "title": title % opts.verbose_name,
            "adminform": adminForm,
            "object_id": object_id,
            "original": obj,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "media": media,
            "inline_admin_formsets": inline_formsets,
            "errors": helpers.AdminErrorList(form, formsets),
            "preserved_filters": self.get_preserved_filters(request),
            "show_save_and_continue": False,
        }

        context.update(extra_context or {})

        return self.render_change_form(
            request, context, add=add, change=not add, obj=obj, form_url=form_url
        )

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determine the HttpResponse for the add_view stage.
        """
        # Copied from django.contrib.admin.options.py
        opts = obj._meta
        preserved_filters = self.get_preserved_filters(request)
        msg_dict = {
            "name": opts.verbose_name,
        }

        if "_addanother" in request.POST:
            msg = format_html(_(self.get_first_phrase()), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        msg = format_html(
            _(
                self.get_first_phrase()
                + " The task might already have finished, for that its entry can already appear on the list below."
            ),
            **msg_dict,
        )
        self.message_user(request, msg, messages.SUCCESS)
        return self.response_post_save_add(request, obj)

    def response_change(self, request, obj):
        """
        Determine the HttpResponse for the change_view stage.
        """
        # Copied from django.contrib.admin.options.py

        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        msg_dict = {
            "name": opts.verbose_name,
            # "obj": format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
        }

        if "_addanother" in request.POST:
            msg = format_html(_(self.get_first_phrase()), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = reverse(
                "admin:%s_%s_add" % (opts.app_label, opts.model_name),
                current_app=self.admin_site.name,
            )
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        msg = format_html(
            _(
                self.get_first_phrase()
                + " The task might already have finished, for that its entry can already appear on the list below."
            ),
            **msg_dict,
        )
        self.message_user(request, msg, messages.SUCCESS)
        return self.response_post_save_change(request, obj)

    def get_first_phrase(self):
        if hasattr(self, "background_task"):
            background_task_id = getattr(self, "background_task").id
            try:
                task_url = reverse(
                    "admin:%s_%s_change"
                    % (TaskResult._meta.app_label, TaskResult._meta.model_name),
                    args=(
                        quote(TaskResult.objects.get(task_id=background_task_id).pk),
                    ),
                    current_app=self.admin_site.name,
                )
            except TaskResult.DoesNotExist:
                tasks_results_url = reverse(
                    f"admin:{TaskResult._meta.app_label}_{TaskResult._meta.model_name}_changelist",
                    current_app=self.admin_site.name,
                )
                return (
                    f'The {{name}} is being created on the background task with id "{background_task_id}", '
                    "which you can see its status after a couple of seconds on the "
                    f'<a href="{tasks_results_url}">Celery Results app</a>.'
                )
            else:
                link = format_html(
                    '<a href="{}">{}</a>', urlquote(task_url), background_task_id
                )

                return f"The {{name}} is being created on the background task {link}."

        return "The {name} is being created on a background task."
