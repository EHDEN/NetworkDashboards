from contextlib import closing

from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import flatten_fieldsets, unquote
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db import connections, ProgrammingError
from django.forms import all_valid
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
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

    def delete_queryset(self, request, queryset):
        with closing(connections["achilles"].cursor()) as cursor:
            for obj in queryset:
                try:
                    cursor.execute(
                        f"DROP MATERIALIZED VIEW {obj.name}"
                    )  # Ignore if the view doesn't exist
                except ProgrammingError:
                    pass
        super().delete_queryset(request, queryset)

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
                # self.save_model(request, new_object, form, not add)
                # self.save_related(request, form, formsets, not add)
                if add:
                    # self.log_addition(request, new_object, change_message)
                    return self.response_add(request, new_object)
                # self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)
            # else:
            #     form_validated = False
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

        # Hide the "Save" and "Save and continue" buttons if "Save as New" was
        # previously chosen to prevent the interface from getting confusing.
        # if request.method == 'POST' and not form_validated and "_saveasnew" in request.POST:
        #    context['show_save'] = False
        #    context['show_save_and_continue'] = False
        #    # Use the change template instead of the add template.
        #    add = False

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
        # obj_url = reverse(
        #    'admin:%s_%s_change' % (opts.app_label, opts.model_name),
        #    args=(quote(obj.pk),),
        #    current_app=self.admin_site.name,
        #    )
        ## Add a link to the object's change form if the user can edit the obj.
        # if self.has_change_permission(request, obj):
        #    obj_repr = format_html('<a href="{}">{}</a>', urlquote(obj_url), obj)
        # else:
        #    obj_repr = str(obj)
        msg_dict = {
            "name": opts.verbose_name,
            # "obj": obj_repr,
        }
        # Here, we distinguish between different save types by checking for
        # the presence of keys in request.POST.

        # if IS_POPUP_VAR in request.POST:
        #    to_field = request.POST.get(TO_FIELD_VAR)
        #    if to_field:
        #        attr = str(to_field)
        #    else:
        #        attr = obj._meta.pk.attname
        #    value = obj.serializable_value(attr)
        #    popup_response_data = json.dumps({
        #        'value': str(value),
        #        'obj': str(obj),
        #    })
        #    return TemplateResponse(request, self.popup_response_template or [
        #        'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
        #        'admin/%s/popup_response.html' % opts.app_label,
        #        'admin/popup_response.html',
        #        ], {
        #                                'popup_response_data': popup_response_data,
        #                            })

        # elif "_continue" in request.POST or (
        #        # Redirecting after "Save as new".
        #        "_saveasnew" in request.POST and self.save_as_continue and
        #        self.has_change_permission(request, obj)
        # ):
        #    msg = _('The {name} "{obj}" was added successfully.')
        #    if self.has_change_permission(request, obj):
        #        msg += ' ' + _('You may edit it again below.')
        #    self.message_user(request, format_html(msg, **msg_dict), messages.SUCCESS)
        #    if post_url_continue is None:
        #        post_url_continue = obj_url
        #    post_url_continue = add_preserved_filters(
        #        {'preserved_filters': preserved_filters, 'opts': opts},
        #        post_url_continue
        #    )
        #    return HttpResponseRedirect(post_url_continue)
        # elif "_addanother" in request.POST:
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

        # if IS_POPUP_VAR in request.POST:
        #    opts = obj._meta
        #    to_field = request.POST.get(TO_FIELD_VAR)
        #    attr = str(to_field) if to_field else opts.pk.attname
        #    value = request.resolver_match.kwargs['object_id']
        #    new_value = obj.serializable_value(attr)
        #    popup_response_data = json.dumps({
        #        'action': 'change',
        #        'value': str(value),
        #        'obj': str(obj),
        #        'new_value': str(new_value),
        #    })
        #    return TemplateResponse(request, self.popup_response_template or [
        #        'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
        #        'admin/%s/popup_response.html' % opts.app_label,
        #        'admin/popup_response.html',
        #        ], {
        #                                'popup_response_data': popup_response_data,
        #                            })

        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        msg_dict = {
            "name": opts.verbose_name,
            # "obj": format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
        }
        # if "_continue" in request.POST:
        #    msg = format_html(
        #        _('The {name} "{obj}" was changed successfully. You may edit it again below.'),
        #        **msg_dict
        #    )
        #    self.message_user(request, msg, messages.SUCCESS)
        #    redirect_url = request.path
        #    redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
        #    return HttpResponseRedirect(redirect_url)
        # elif "_saveasnew" in request.POST:
        #    msg = format_html(
        #        _('The {name} was changed successfully. You may edit it again below.'),
        #        **msg_dict
        #    )
        #    self.message_user(request, msg, messages.SUCCESS)
        #    redirect_url = reverse('admin:%s_%s_change' %
        #                           (opts.app_label, opts.model_name),
        #                           args=(obj.pk,),
        #                           current_app=self.admin_site.name)
        #    redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
        #    return HttpResponseRedirect(redirect_url)
        # elif "_addanother" in request.POST:
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
            tasks_results_url = reverse(
                f"admin:{TaskResult._meta.app_label}_{TaskResult._meta.model_name}_changelist",
                current_app=self.admin_site.name,
            )
            background_task = getattr(self, "background_task")
            return (
                f'The {{name}} is being created on the background task with id "{background_task}", '
                "which you can see its status after a couple of seconds on the "
                f'<a href="{tasks_results_url}">Celery Results app</a>.'
            )

        return "The {name} is being created on a background task."
