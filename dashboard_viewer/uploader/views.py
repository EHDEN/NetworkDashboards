
from typing import Union
import datetime
import os

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


def get_df_from_uploaded_file(request: WSGIRequest) -> Union[pandas.DataFrame, None]:
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


    missing = []  # noqa
    if achilles_results[achilles_results.analysis_id == 0].empty:
        missing.append("0")
    if achilles_results[achilles_results.analysis_id == 5000].empty:
        missing.append("5000")

    if missing:
        missing = f"{missing[0]} is" if len(missing) == 1 else f"{', '.join(missing[:-1])} and {missing[-1]} are"

        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                f"Analysis id {missing} missing. Try (re)running the plugin"
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                "on your database."
            ),
        )

        return

    return achilles_results


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
            achilles_results = get_df_from_uploaded_file(request)

            if achilles_results:
                # launch an asynchronous task
                update_achilles_results_data.delay(
                    obj_data_source.id,
                    upload_history[0].id if len(upload_history) > 0 else None,
                    achilles_results.to_json(),
                )

                # TODO aspedrosa: fill with appropriate data
                latest_upload = UploadHistory(
                    data_source=obj_data_source,
                    upload_date=datetime.datetime.today(),
                    achilles_version="3.3.3",#achilles_version,
                    achilles_generation_date=datetime.datetime.today(),#datachilles_generation_date,
                    cdm_version="3.5.5",#cdm_version,
                    vocabulary_version="3.3.3",#form.cleaned_data["vocabulary_version"],
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
                achilles_results.to_csv(
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
