import csv
import datetime
import io
import os

import constance
import numpy  # noqa
import pandas
from django.conf import settings
from django.contrib import messages
from django.forms import fields
from django.shortcuts import redirect, render
from django.utils.html import format_html, mark_safe
from django.views.decorators.csrf import csrf_exempt

from .forms import AchillesResultsForm, SourceForm
from .models import Country, DataSource, UploadHistory
from .tasks import update_achilles_results_data

PAGE_TITLE = "Dashboard Data Upload"


def _check_correct(names, values, check, transform=None):
    """
    Transforms the values of given fields from the uploaded file
     and check if they end up in the desired format

    :param names: names of the fields to check
    :param values: values of the fields to transform and check if they are
     in the right format
    :param transform: callable to transform the values of the
     provided fields
    :param check: callable check if the transform processes generated
     a valid output
    :return: the transformed fields or an error string
    """
    assert len(names) == len(values)

    transformed_elements = [None] * len(names)
    bad_elements = []

    for i, name in enumerate(names):
        transformed = values[i] if not transform else transform(values[i])
        if not check(transformed):
            bad_elements.append(name)
        else:
            transformed_elements[i] = transformed

    if bad_elements:
        return (
            f" {bad_elements[0]} is"
            if len(bad_elements) == 1
            else f"s {', '.join(bad_elements[:-1])} and {bad_elements[-1]} are"
        )

    return transformed_elements


def _extract_data_from_uploaded_file(request):
    columns = [
        "analysis_id",
        "stratum_1",
        "stratum_2",
        "stratum_3",
        "stratum_4",
        "stratum_5",
        "count_value",
    ]

    wrapper = io.TextIOWrapper(request.FILES["results_file"])
    csv_reader = csv.reader(wrapper)

    first_row = next(csv_reader)
    wrapper.detach()

    if len(first_row) == 16:
        columns.extend(
            [
                "min_value",
                "max_value",
                "avg_value",
                "stdev_value",
                "median_value",
                "p10_value",
                "p25_value",
                "p75_value",
                "p90_value",
            ]
        )
    elif len(first_row) != 7:
        messages.error(
            request,
            mark_safe("The provided file has an invalid number of columns."),
        )

        return None

    request.FILES["results_file"].seek(0)

    try:
        achilles_results = pandas.read_csv(
            request.FILES["results_file"],
            header=0,
            dtype=str,
            skip_blank_lines=False,
            index_col=False,
            names=columns,
        )
    except ValueError:
        messages.error(
            request,
            mark_safe(
                "The provided file has an invalid csv format. Make sure is a text file separated"
                " by <b>commas</b> and you either have 7 (regular results file) or 13 (results file"
                " with dist columns) columns."
            ),
        )

        return None

    if achilles_results[["analysis_id", "count_value"]].isna().values.any():
        messages.error(
            request,
            mark_safe(
                'Some rows have null values either on the column "analysis_id" or "count_value".'
            ),
        )

        return None

    try:
        achilles_results = achilles_results.astype(
            {
                "analysis_id": numpy.int64,
                "count_value": numpy.int64,
            },
        )
        if len(achilles_results.columns) == 16:
            achilles_results = achilles_results.astype(
                {
                    "min_value": float,
                    "max_value": float,
                    "avg_value": float,
                    "stdev_value": float,
                    "median_value": float,
                    "p10_value": float,
                    "p25_value": float,
                    "p75_value": float,
                    "p90_value": float,
                },
            )
    except ValueError:
        messages.error(
            request,
            mark_safe(
                'The provided file has invalid values on some columns. Remember that only the "stratum_*" columns'
                " accept strings, all the other fields expect numeric types."
            ),
        )

        return None

    analysis_0 = achilles_results[achilles_results.analysis_id == 0]
    if analysis_0.empty:
        messages.error(
            request,
            mark_safe(
                f"Analysis id 0 is missing. Try (re)running the plugin "
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            ),
        )

        return None

    analysis_0 = analysis_0.reset_index()
    analysis_5000 = achilles_results[achilles_results.analysis_id == 5000].reset_index()

    output = _check_correct(
        ["0"] + (["5000"] if not analysis_5000.empty else []),
        [analysis_0] + ([analysis_5000] if not analysis_5000.empty else []),
        lambda e: len(e) == 1,
    )
    if isinstance(output, str):
        messages.error(
            request,
            mark_safe(
                f"Analysis id{output} duplicated on multiple rows. Try (re)running the plugin "
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            ),
        )
        return None

    return {
        "achilles_results": achilles_results,
        "generation_date": analysis_0.loc[0, "stratum_3"],
        "source_release_date": analysis_5000.loc[0, "stratum_2"]
        if not analysis_5000.empty
        else None,
        "cdm_release_date": analysis_5000.loc[0, "stratum_3"]
        if not analysis_5000.empty
        else None,
        "cdm_version": analysis_5000.loc[0, "stratum_4"]
        if not analysis_5000.empty
        else None,
        "r_package_version": analysis_0.loc[0, "stratum_2"],
        "vocabulary_version": analysis_5000.loc[0, "stratum_5"]
        if not analysis_5000.empty
        else None,
    }


@csrf_exempt
def upload_achilles_results(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        obj_data_source = DataSource.objects.get(acronym=data_source)
    except DataSource.DoesNotExist:
        return create_data_source(request, *args, **kwargs)

    upload_history = list(
        UploadHistory.objects.filter(data_source__acronym=obj_data_source.acronym)
    )
    if request.method == "GET":
        form = AchillesResultsForm()

    elif request.method == "POST":
        form = AchillesResultsForm(request.POST, request.FILES)

        if form.is_valid():
            data = _extract_data_from_uploaded_file(request)

            if data:
                # launch an asynchronous task to insert the new data
                update_achilles_results_data.delay(
                    obj_data_source.id,
                    upload_history[0].id if len(upload_history) > 0 else None,
                    data["achilles_results"].to_json(),
                )

                obj_data_source.release_date = data["source_release_date"]
                obj_data_source.save()

                latest_upload = UploadHistory(
                    data_source=obj_data_source,
                    upload_date=datetime.datetime.today(),
                    r_package_version=data["r_package_version"],
                    generation_date=data["generation_date"],
                    cdm_release_date=data["cdm_release_date"],
                    cdm_version=data["cdm_version"],
                    vocabulary_version=data["vocabulary_version"],
                )
                latest_upload.save()
                upload_history = [latest_upload] + upload_history

                # save the achilles result file to disk
                data_source_storage_path = os.path.join(
                    settings.BASE_DIR,
                    settings.ACHILLES_RESULTS_STORAGE_PATH,
                    obj_data_source.acronym,
                )
                os.makedirs(data_source_storage_path, exist_ok=True)
                data["achilles_results"].to_csv(
                    os.path.join(
                        data_source_storage_path, f"{len(upload_history)}.csv"
                    ),
                    index=False,
                )

                messages.success(
                    request,
                    "Results file uploaded with success. The dashboards will update in a few minutes.",
                )

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


def _get_fields_initial_values(request, initial):
    for field_name, field in SourceForm.base_fields.items():
        if isinstance(field, fields.MultiValueField):
            for i in range(len(field.widget.widgets)):
                generated_field_name = f"{field_name}_{i}"
                field_value = request.GET.get(generated_field_name)
                if field_value:
                    initial[generated_field_name] = field_value
        elif field_name == "country":
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
            if field_name in aux_form.cleaned_data:
                initial[field_name] = aux_form.cleaned_data[field_name]
            elif field_name in initial:
                del initial[field_name]


@csrf_exempt
def create_data_source(request, *_, **kwargs):
    data_source = kwargs.get("data_source")
    if request.method == "GET":
        initial = {"acronym": data_source}

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

                return redirect("/uploader/{}".format(obj.acronym))

            # since the form isn't valid, lets maintain only the valid fields
            _leave_valid_fields_values_only(request, initial, aux_form)

            form = SourceForm(initial=initial)

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
            form.fields["acronym"].disabled = True
    elif request.method == "POST":
        post_data = request.POST.copy()
        if "acronym" not in post_data and data_source is not None:
            post_data.update({"acronym": data_source})

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
            return redirect("/uploader/{}".format(obj.acronym))

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
        data_source = DataSource.objects.get(acronym=data_source)
    except DataSource.DoesNotExist:
        messages.error(
            request,
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

            messages.success(
                request,
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
            "constance_config": constance.config,
            "page_title": PAGE_TITLE,
        },
    )
