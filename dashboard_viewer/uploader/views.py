import itertools

import constance
from django.contrib import messages
from django.forms import fields
from django.shortcuts import redirect, render
from django.utils.html import format_html, mark_safe
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .forms import AchillesResultsForm, EditSourceForm, SourceForm
from .models import Country, DataSource, UploadHistory, PendingUpload
from .serializers import DataSourceSerializer
from .tasks import upload_results_file

PAGE_TITLE = "Dashboard Data Upload"


@csrf_exempt
def upload_achilles_results(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        obj_data_source = DataSource.objects.get(hash=data_source)
    except DataSource.DoesNotExist:
        return create_data_source(request, *args, **kwargs)

    upload_history = UploadHistory.objects.filter(data_source=obj_data_source)
    pending_upload_history = PendingUpload.objects.filter(data_source=obj_data_source)

    if request.method == "GET":
        form = AchillesResultsForm()

    elif request.method == "POST":
        form = AchillesResultsForm(request.POST, request.FILES)

        if form.is_valid():
            pending_upload = PendingUpload.objects.create(
                data_source=obj_data_source,
                uploaded_file=request.FILES["results_file"]
            )

            pending_upload_history = itertools.chain(pending_upload, pending_upload_history)

            messages.success(request, "A background task back processing the uploaded file. You can check its status on the Pending uploads tab")

            upload_results_file.delay(pending_upload.id)

    return render(
        request,
        "upload_achilles_results.html",
        {
            "form": form,
            "obj_data_source": obj_data_source,
            "upload_history": upload_history,
            "pending_uploads_history": pending_upload_history,
            "submit_button_text": mark_safe("<i class='fas fa-upload'></i> Upload"),
            "constance_config": constance.config,
            "page_title": PAGE_TITLE,
        },
    )


def _get_fields_initial_values(request, initial):
    for field_name, field in SourceForm.base_fields.items():
        if isinstance(field, fields.MultiValueField):
            for i in range(len(field.widget.widgets)):
                generated_field_name = f"{field_name}_{i}"
                field_value = request.GET.get(generated_field_name)
                if field_value:
                    initial[generated_field_name] = field_value
        elif field_name == "country" and "country" in request.GET:
            countries_found = Country.objects.filter(
                country__icontains=request.GET["country"]
            )
            if countries_found.count() == 1:
                initial["country"] = countries_found.get().id
        else:
            field_value = request.GET.get(field_name)
            if field_value:
                initial[field_name] = field_value


def _leave_valid_fields_values_only(request, initial, aux_form):
    for field_name, field in SourceForm.base_fields.items():
        if isinstance(field, fields.MultiValueField):
            decompressed = list()

            for i in range(len(field.widget.widgets)):
                generated_field_name = f"{field_name}_{i}"
                value = request.GET.get(generated_field_name)
                if value:
                    del initial[generated_field_name]
                    decompressed.append(value)
                else:
                    decompressed = list()
                    break

            if decompressed:
                initial[field_name] = field.compress(decompressed)
        else:
            if (
                field_name in aux_form.cleaned_data
                and aux_form.cleaned_data[field_name] not in field.empty_values
            ):
                initial[field_name] = aux_form.cleaned_data[field_name]
            elif field_name in initial:
                del initial[field_name]


@csrf_exempt
def create_data_source(request, *_, **kwargs):
    data_source = kwargs.get("data_source")
    if request.method == "GET":
        initial = dict()
        if data_source is not None:
            initial["hash"] = data_source

        if request.GET:  # if the request has arguments
            # compute fields' initial values
            _get_fields_initial_values(request, initial)

            aux_form = SourceForm(initial)
            if aux_form.is_valid():
                obj = aux_form.save(commit=False)
                lat, lon = aux_form.cleaned_data["coordinates"].split(",")
                obj.latitude, obj.longitude = float(lat), float(lon)
                obj.data_source = data_source
                obj.save()

                return redirect("/uploader/{}".format(obj.hash))

            # since the form isn't valid, lets maintain only the valid fields
            _leave_valid_fields_values_only(request, initial, aux_form)

            form = SourceForm(initial=initial)
            for key in initial:
                form.fields[key].widget.attrs["readonly"] = True

            # fill the form with errors associated with each field that wasn't valid
            # for field, msgs in aux_form.errors.items():
            #    required_error = False
            #    for msg in msgs:
            #        if "required" in msg:
            #            required_error = True
            #            break

            #    if not required_error:
            #        form.errors[field] = msgs
        else:
            form = SourceForm(initial=initial)

        if data_source is not None:
            form.fields["hash"].disabled = True
    elif request.method == "POST":
        post_data = request.POST.copy()
        if "hash" not in post_data and data_source is not None:
            post_data.update({"hash": data_source})

        form = SourceForm(post_data)
        if form.is_valid():
            obj = form.save(commit=False)
            lat, lon = form.cleaned_data["coordinates"].split(",")
            obj.latitude, obj.longitude = float(lat), float(lon)
            obj.data_source = data_source
            obj.save()

            messages.success(
                request,
                format_html(
                    "Data source <b>{}</b> created with success. You may now upload results files.",
                    obj.name,
                ),
            )
            return redirect("/uploader/{}".format(obj.hash))

    return render(
        request,
        "data_source.html",
        {
            "form": form,
            "editing": False,
            "submit_button_text": mark_safe(
                "<i class='fas fa-plus-circle'></i> Create"
            ),
            "constance_config": constance.config,
            "page_title": PAGE_TITLE,
        },
    )


@csrf_exempt
def edit_data_source(request, *_, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        data_source = DataSource.objects.get(hash=data_source)
    except DataSource.DoesNotExist:
        messages.error(
            request,
            format_html("No data source with the hash <b>{}</b>", data_source),
        )

        return redirect("/uploader/")

    if request.method == "GET":
        form = EditSourceForm(
            initial={
                "name": data_source.name,
                "release_date": data_source.release_date,
                "database_type": data_source.database_type,
                "country": data_source.country,
                "coordinates": f"{data_source.latitude},{data_source.longitude}",
                "link": data_source.link,
                "draft": data_source.draft,
            }
        )
    elif request.method == "POST":
        form = EditSourceForm(request.POST, instance=data_source)
        if form.is_valid():
            obj = form.save(commit=False)
            lat, lon = form.cleaned_data["coordinates"].split(",")
            obj.latitude, obj.longitude = float(lat), float(lon)
            obj.save()

            messages.success(
                request,
                format_html("Data source <b>{}</b> edited with success.", obj.name),
            )
            return redirect("/uploader/{}".format(obj.hash))

    return render(
        request,
        "data_source.html",
        {
            "form": form,
            "editing": True,
            "submit_button_text": mark_safe("<i class='far fa-edit'></i> Edit"),
            "constance_config": constance.config,
            "page_title": PAGE_TITLE,
        },
    )


class DataSourceUpdate(GenericViewSet):
    # since the edit and upload views have not authentication, also disable
    #  authentication from this
    authentication_classes = ()
    permission_classes = ()

    lookup_field = "hash"
    serializer_class = DataSourceSerializer
    queryset = DataSource.objects.all()

    def partial_update(self, request, *_, **__):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}  # noqa

        return Response(serializer.data)
