
import datetime
import os
import re

from django.conf import settings
from django.contrib import messages
from django.forms import fields
from django.shortcuts import redirect, render
from django.utils.html import format_html, mark_safe
from django.views.decorators.csrf import csrf_exempt

from .forms import SourceForm, AchillesResultsForm
from .models import UploadHistory, DataSource
from .tasks import update_achilles_results_data


quotes_regex = re.compile(r"^'|'$|^\"|\"$")


@csrf_exempt
def upload_achilles_results(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        obj_data_source = DataSource.objects.get(acronym=data_source)
    except DataSource.DoesNotExist:
        return create_data_source(request, *args, **kwargs)

    upload_history = list(UploadHistory.objects.filter(data_source__acronym=obj_data_source.acronym))
    if request.method == "GET":
        form = AchillesResultsForm()

    elif request.method == "POST":
        form = AchillesResultsForm(request.POST, request.FILES)

        if form.is_valid():
            error = None
            uploadedFile = request.FILES["achilles_results"]

            if uploadedFile.content_type == "text/csv":
                file_content = uploadedFile.read()
                lines = file_content.decode("UTF-8").split("\n")
                for i, line in enumerate(lines):
                    lines[i] = [re.sub(quotes_regex, "", entry) for entry in line.strip().split(",")]
                    if len(lines[i]) != 7 and (i != len(lines) - 1 or line != ""):
                        # fail if the number of columns is not 7 and if the its not the last line
                        # or if it is the last line and is not a empty line. This condition allows
                        # and empty line on the last line.
                        error = mark_safe(f"Invalid number of columns on line {i + 1}. The csv file"
                                          f" uploaded must have <b>seven</b> columns (analysis_id,"
                                          f" stratum_1, stratum_2, stratum_3, stratum_4, stratum_5, count_value).")
                        break

                if form.cleaned_data["has_header"]:
                    lines = lines[1:]

                # if the last line is a empty line remove it
                if len(lines[-1]) == 1:
                    lines = lines[:-1]

            else:
                error = mark_safe("Uploaded achilles results files should be <b>CSV</b> files.")

            # get the latest upload record on the upload history
            uploads = UploadHistory.objects.filter(data_source__slug=obj_data_source.slug).order_by('-upload_date')

            if not error:
                # launch a asynchronous task
                update_achilles_results_data.delay(
                    obj_data_source.id,
                    uploads[0].id if len(uploads) > 0 else None,
                    lines,
                )

                lines = None

                latest_upload = UploadHistory(
                    data_source=obj_data_source,
                    upload_date=datetime.datetime.today(),
                    achilles_version=form.cleaned_data["achilles_version"],
                    achilles_generation_date=form.cleaned_data["achilles_generation_date"],
                    cdm_version=form.cleaned_data["cdm_version"],
                    vocabulary_version=form.cleaned_data["vocabulary_version"],
                )
                latest_upload.save()
                upload_history = [latest_upload] + list(uploads)

                # save the achilles result file to disk
                data_source_storage_path = os.path.join(
                    settings.BASE_DIR,
                    settings.ACHILLES_RESULTS_STORAGE_PATH,
                    obj_data_source.acronym
                )
                os.makedirs(data_source_storage_path, exist_ok=True)
                f = open(os.path.join(data_source_storage_path, f"{len(uploads)}.csv"), "wb+")
                f.write(file_content)
                f.close()

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Achilles Results file uploaded with success. The dashboards will update in a few minutes.",
                )

                form = AchillesResultsForm()

            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    error,
                )

                upload_history = list(uploads)
    return render(
        request,
        'upload_achilles_results.html',
        {
            "form": form,
            "obj_data_source": obj_data_source,
            "upload_history": upload_history,
            "submit_button_text": mark_safe("<i class='fas fa-upload'></i> Upload"),
        }
    )


@csrf_exempt
def create_data_source(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    if request.method == "GET":
        if request.GET:
            initial = dict()
            for field_name, field in SourceForm.base_fields.items():
                if isinstance(field, fields.MultiValueField):
                    for i, widget in enumerate(field.widget.widgets):
                        generated_field_name = f"{field_name}_{i}"
                        field_value = request.GET.get(generated_field_name)
                        if field_value:
                            initial[generated_field_name] = field_value
                else:
                    field_value = request.GET.get(field_name)
                    if field_value:
                        initial[field_name] = field_value

            aux_form = SourceForm(initial)
            if aux_form.is_valid():
                obj = aux_form.save(commit=False)
                lat, lon = aux_form.cleaned_data["coordinates"].split(",")
                obj.latitude, obj.longitude = float(lat), float(lon)
                obj.data_source = data_source
                obj.save()

                return redirect("/uploader/{}".format(obj.acronym))


            for field_name, field in SourceForm.base_fields.items():
                if isinstance(field, fields.MultiValueField):
                    decompressed = list()

                    for i, _ in enumerate(field.widget.widgets):
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
                    if field_name in aux_form.cleaned_data:
                        initial[field_name] = aux_form.cleaned_data[field_name]

            form = SourceForm(initial=initial)

            for field, msgs in aux_form.errors.items():
                required_error = False
                for msg in msgs:
                    if "required" in msg:
                        required_error = True
                        break

                if not required_error:
                    form.errors[field] = msgs
        else:
            form = SourceForm(initial={"acronym": data_source})

        if data_source is not None:
            form.fields["acronym"].disabled = True
    elif request.method == "POST":
        if "acronym" not in request.POST and data_source is not None:
            request.POST["acronym"] = data_source

        form = SourceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            lat, lon = form.cleaned_data["coordinates"].split(",")
            obj.latitude, obj.longitude = float(lat), float(lon)
            obj.data_source = data_source
            obj.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                format_html(
                    "Data source <b>{}</b> created with success. You may now upload achilles results files.",
                    obj.name
                ),
            )
            return redirect("/uploader/{}".format(obj.acronym))
        
    return render(
        request,
        "data_source.html",
        {
            "form": form,
            "editing": False,
            "submit_button_text": mark_safe("<i class='fas fa-plus-circle'></i> Create"),
        }
    )


@csrf_exempt
def edit_data_source(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        data_source = DataSource.objects.get(acronym=data_source)
    except DataSource.DoesNotExist:
        messages.add_message(
            request,
            messages.ERROR,
            format_html("No data source with the acronym <b>{}</b>", data_source),
        )

        return redirect("/uploader/")

    if request.method == "GET":
        form = SourceForm(
            initial={
                "name": data_source.name,
                "acronym": data_source.acronym,
                "release_date": data_source.release_date,
                "database_type": data_source.database_type,
                "country": data_source.country,
                "coordinates": f"{data_source.latitude},{data_source.longitude}",
                "link": data_source.link,
            }
        )
        form.fields["acronym"].disabled = True
    elif request.method == "POST":
        form = SourceForm(request.POST, instance=data_source)
        form.fields["acronym"].disabled = True
        if form.is_valid():
            obj = form.save(commit=False)
            lat, lon = form.cleaned_data["coordinates"].split(",")
            obj.latitude, obj.longitude = float(lat), float(lon)
            obj.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                format_html("Data source <b>{}</b> edited with success.", obj.name),
            )
            return redirect("/uploader/{}".format(obj.acronym))

    return render(
        request,
        "data_source.html",
        {
            "form": form,
            "editing": True,
            "submit_button_text": mark_safe("<i class='far fa-edit'></i> Edit"),
        }
    )
