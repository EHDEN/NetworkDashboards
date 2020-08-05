
from typing import Union, List, Dict, Any
import datetime
import os
import re

from django.conf import settings
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import redirect, render
from django.utils.html import format_html, mark_safe
from django.views.decorators.csrf import csrf_exempt
import pandas
import numpy  # noqa

from .forms import SourceFrom, AchillesResultsForm
from .models import UploadHistory, DataSource
from .tasks import update_achilles_results_data


VERSION_REGEX = re.compile(r'[\d.]*\d+')


def convert_to_datetime_from_iso(elem):
    analysis, stratum = elem

    try:
        return datetime.datetime.fromisoformat(analysis.loc[0, stratum])
    except ValueError:
        return None


def check_correct(names: List[str], values: List[Any], transform, check) -> Union[List[Any], str]:
    assert len(names) == len(values)

    transformed_elements = [None] * len(names)
    bad_elements = []

    for i in range(len(names)):
        transformed = transform(values[i])
        if not check(transformed):
            bad_elements.append(names[i])
        else:
            transformed_elements[i] = transformed

    if bad_elements:
        return f" {bad_elements[0]} is" if len(bad_elements) == 1 else f"s {', '.join(bad_elements[:-1])} and {bad_elements[-1]} are"

    return transformed_elements


def extract_data_from_uploaded_file(request: WSGIRequest) -> Union[Dict, None]:
    try:
        achilles_results = pandas.read_csv(
            request.FILES["achilles_results_file"],
            header=0,
            usecols=range(7),
            dtype=str,
            low_memory=False,
        )
    except ValueError:
        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                "The provided file has an invalid csv format. Make sure is a text file separated"
                " by <b>commas</b> with <b>seven</b> columns (analysis_id, stratum_1,"
                " stratum_2, stratum_3, stratum_4, stratum_5, count_value)."
            ),
        )

        return


    achilles_results.columns = [  # noqa
        "analysis_id",
        "stratum_1",
        "stratum_2",
        "stratum_3",
        "stratum_4",
        "stratum_5",
        "count_value"
    ]

    try:
        achilles_results.astype({
            "analysis_id": numpy.int32,
            "count_value": numpy.int32,
        }, copy=False)
    except ValueError:
        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                "The provided file has invalid values on the columns <i>analysis_id</i> or <i>count_value</i>."
                " These must be integers."
            ),
        )

        return

    output = check_correct(
        ["0", "5000"],
        [0, 5000],
        lambda e: achilles_results[achilles_results.analysis_id == e],
        lambda e: e.empty
    )

    if isinstance(output, str):
        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                f"Analysis id{output} missing. Try (re)running the plugin"
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                "on your database."
            ),
        )

        return

    return_value = {"achilles_results": achilles_results}

    analysis_0 = output[0]
    analysis_5000 = output[1]

    errors = False

    # check dates
    output = check_correct(
        ["Achilles generation date (analysis=0, stratum2)", "CDM release date (analysis=5000, stratum_3)"],
        [(analysis_0, "stratum_2"), (analysis_5000, "stratum_3")],
        convert_to_datetime_from_iso,
        lambda _: True,
    )

    if isinstance(output, str):
        errors = True

        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                f"The field{output} not in a ISO date format."
            ),
        )
    else:
        return_value["achilles_generation_date"] = output[0]
        return_value["cdm_release_date"] = output[1]

    # check versions
    output = check_correct(
        ["CDM version (analysis_id=0, stratum_1)", "Achilles version (analysis_id=5000, stratum_4)"],
        [(analysis_0, "stratum_1"), (analysis_5000, "stratum_4")],
        lambda elem: elem[0].loc[0, elem[1]],
        VERSION_REGEX.match,
    )

    if isinstance(output, str):
        errors = True
        
        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                f"The field{output} not in valid version format. Should match the regex '[\\d.]*\\d+'."
            ),
        )
    else:
        return_value["cdm_version"] = output[0]
        return_value["achilles_version"] = output[1]

    if errors:
        return

    return return_value


@csrf_exempt
def upload_achilles_results(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        obj_data_source = DataSource.objects.get(slug=data_source)
    except DataSource.DoesNotExist:
        return create_data_source(request, *args, **kwargs)

    upload_history = list(UploadHistory.objects.filter(data_source__slug=obj_data_source.slug))
    if request.method == "GET":
        form = AchillesResultsForm()

    elif request.method == "POST":
        form = AchillesResultsForm(request.POST, request.FILES)

        if form.is_valid():
            data = extract_data_from_uploaded_file(request)

            if data:

                # launch an asynchronous task
                update_achilles_results_data.delay(
                    obj_data_source.id,
                    upload_history[0].id if len(upload_history) > 0 else None,
                    data["achilles_results"].to_json(),
                )

                latest_upload = UploadHistory(
                    data_source=obj_data_source,
                    upload_date=datetime.datetime.today(),
                    achilles_version=data["achilles_version"],
                    achilles_generation_date=data["achilles_generation_date"],
                    cdm_release_date=data["cdm_release_date"],
                    cdm_version=data["cdm_version"],
                    vocabulary_version=data["cdm_version"],  # TODO aspedrosa: change this
                )
                latest_upload.save()
                upload_history = [latest_upload] + upload_history

                # save the achilles result file to disk
                data_source_storage_path = os.path.join(
                    settings.BASE_DIR,
                    settings.ACHILLES_RESULTS_STORAGE_PATH,
                    obj_data_source.slug
                )
                os.makedirs(data_source_storage_path, exist_ok=True)
                data["achilles_results"].to_csv(
                    os.path.join(
                        data_source_storage_path,
                        f"{len(upload_history)}.csv"
                    ),
                    index=False,
                )

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Achilles Results file uploaded with success. The dashboards will update in a few minutes.",
                )

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
        form = SourceFrom(initial={'slug': data_source})
        if data_source is not None:
            form.fields["slug"].disabled = True
    elif request.method == "POST":
        if "slug" not in request.POST and data_source is not None:
            request.POST = request.POST.copy()
            request.POST["slug"] = data_source
        form = SourceFrom(request.POST)
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
            return redirect("/uploader/{}".format(obj.slug))
        
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
        data_source = DataSource.objects.get(slug=data_source)
    except DataSource.DoesNotExist:
        messages.add_message(
            request,
            messages.ERROR,
            format_html("No data source with the slug <b>{}</b>", data_source),
        )

        return redirect("/uploader/")

    if request.method == "GET":
        form = SourceFrom(
            initial= {
                "name": data_source.name,
                "slug": data_source.slug,
                "release_date": data_source.release_date,
                "database_type": data_source.database_type,
                "country": data_source.country,
                "coordinates": f"{data_source.latitude},{data_source.longitude}",
                "link": data_source.link,
            }
        )
        form.fields["slug"].disabled = True
    elif request.method == "POST":
        form = SourceFrom(request.POST, instance=data_source)
        form.fields["slug"].disabled = True
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
            return redirect("/uploader/{}".format(obj.slug))

    return render(
        request,
        "data_source.html",
        {
            "form": form,
            "editing": True,
            "submit_button_text": mark_safe("<i class='far fa-edit'></i> Edit"),
        }
    )
