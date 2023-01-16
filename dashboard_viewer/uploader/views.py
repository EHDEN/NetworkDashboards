import itertools

import constance
from django.contrib import messages
from django.db import router, transaction
from django.forms import fields
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html, mark_safe
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework import viewsets
from rest_framework.response import Response

from materialized_queries_manager.models import MaterializedQuery
from materialized_queries_manager.tasks import refresh_materialized_views_task
from . import serializers
from .decorators import uploader_decorator
from .forms import AchillesResultsForm, EditSourceForm, SourceForm
from .models import Country, DataSource, PendingUpload, UploadHistory
from .tasks import upload_results_file

PAGE_TITLE = "Dashboard Data Upload"


@uploader_decorator
@xframe_options_exempt
def upload_achilles_results(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        obj_data_source = DataSource.objects.get(hash=data_source)
    except DataSource.DoesNotExist:
        return create_data_source(request, *args, **kwargs)

    if request.method == "POST":
        form = AchillesResultsForm(request.POST, request.FILES)

        if form.is_valid():
            pending_upload = PendingUpload.objects.create(
                data_source=obj_data_source, uploaded_file=request.FILES["results_file"]
            )

            messages.success(
                request,
                "File uploaded with success. The file is being processed and its status, on the upload history table "
                "should update in the meantime.",
            )

            task = upload_results_file.delay(pending_upload.id)

            pending_upload.task_id = task.task_id
            pending_upload.save()
    else:
        form = AchillesResultsForm()

    upload_history = sorted(
        itertools.chain(
            UploadHistory.objects.filter(data_source=obj_data_source),
            PendingUpload.objects.filter(data_source=obj_data_source),
        ),
        key=lambda upload: upload.upload_date,
        reverse=True,
    )

    upload_history = list(map(lambda obj: (obj, obj.get_status()), upload_history))

    return render(
        request,
        "upload_achilles_results.html",
        {
            "form": form,
            "obj_data_source": obj_data_source,
            "upload_history": upload_history,
            "submit_button_text": mark_safe("<i class='fas fa-upload'></i> Upload"),
            "constance_config": constance.config,
            "page_title": PAGE_TITLE,
        },
    )


def get_upload_task_status(_request, data_source, upload_id):
    data_source = get_object_or_404(DataSource, hash=data_source)

    try:
        pending_upload = PendingUpload.objects.get(
            id=upload_id, data_source=data_source
        )
    except PendingUpload.DoesNotExist:
        # assume if the objects doesn't exist it finished
        upload = get_object_or_404(
            UploadHistory, data_source=data_source, pending_upload_id=upload_id
        )

        return JsonResponse(
            {
                "status": "Done",
                "data": {
                    "r_package_version": upload.r_package_version,
                    "generation_date": upload.generation_date,
                    "cdm_version": upload.cdm_version,
                    "vocabulary_version": upload.vocabulary_version,
                },
            }
        )

    if pending_upload.status != PendingUpload.STATE_FAILED:
        return JsonResponse({"status": pending_upload.get_status()})

    return JsonResponse(
        {"status": "Failed", "failure_msg": pending_upload.failure_message()}
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
            decompressed = []

            for i in range(len(field.widget.widgets)):
                generated_field_name = f"{field_name}_{i}"
                value = request.GET.get(generated_field_name)
                if value:
                    del initial[generated_field_name]
                    decompressed.append(value)
                else:
                    decompressed = []
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


@uploader_decorator
@xframe_options_exempt
def create_data_source(request, *_, **kwargs):
    data_source = kwargs.get("data_source")
    if request.method == "GET":
        initial = {}
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

                return redirect(f"/uploader/{obj.hash}")

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
            return redirect(f"/uploader/{obj.hash}")

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


@uploader_decorator
@xframe_options_exempt
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
            return redirect(f"/uploader/{obj.hash}")

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


@uploader_decorator
@xframe_options_exempt
def data_source_dashboard(request, data_source):
    try:
        data_source = DataSource.objects.get(hash=data_source)
    except DataSource.DoesNotExist:
        return render(request, "no_uploads_dashboard.html")

    if data_source.uploadhistory_set.exists():
        config = constance.config
        resp = str(
            f"{config.SUPERSET_HOST}/superset/dashboard/{config.DATABASE_DASHBOARD_IDENTIFIER}/"
            "?standalone=1"
            f'&preselect_filters={{"{config.DATABASE_FILTER_ID}":{{"acronym":["{data_source.acronym}"]}}}}'
        )

        return JsonResponse({"link": resp})

    # This way if there is at least one successfull upload it will redirect to the dashboards
    # We could only check if the last upload for the data source was sucessfull
    # -> This will not show data but it can bring a more useful message since the new data may not be processed and the graphics will contain old data
    # -> Perhaps this is the best option has the user will expect the new data to be published and may think the graphics already
    # contain that information

    if not data_source.uploadhistory_set.exists():
        # Check last pending upload for the data source, it may have started but not completed
        try:
            status_of_pd = (
                PendingUpload.objects.filter(data_source_id=data_source.id)
                .values_list("status", flat=True)
                .latest("id")
            )

            if status_of_pd == 2:
                return render(request, "still_processing_achilles.html")

        except PendingUpload.DoesNotExist:
            return render(request, "no_uploads_dashboard.html")

    return render(request, "no_uploads_dashboard.html")


class DataSourceUpdate(viewsets.GenericViewSet):
    # since the edit and upload views don't have authentication, also disable
    #  authentication from this
    authentication_classes = ()
    permission_classes = ()

    lookup_field = "hash"
    serializer_class = serializers.DataSourceSerializer
    queryset = DataSource.objects.all()

    def get_object_for_patch(self):
        # here we get the query set with select_for_update so it lock updates on that record
        queryset = self.filter_queryset(self.get_queryset().select_for_update())

        assert (
            self.lookup_field and not self.lookup_url_kwarg
        ), "Expected lookup_field to be defined and not lookup_url_kwarg."

        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def partial_update(self, request, *_, **__):
        with transaction.atomic(using=router.db_for_write(DataSource)):
            instance = self.get_object_for_patch()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        refresh_materialized_views_task.delay(
            [obj.matviewname for obj in MaterializedQuery.objects.all()],
        )

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}  # noqa

        return Response(serializer.data)
