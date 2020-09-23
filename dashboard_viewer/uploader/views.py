
from typing import Callable, Dict, List, TypeVar, Union
import datetime
import os
import regex

from django.conf import settings
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.forms import fields
from django.shortcuts import redirect, render
from django.utils.html import format_html, mark_safe
from django.views.decorators.csrf import csrf_exempt
import pandas
import numpy  # noqa

from .forms import SourceForm, AchillesResultsForm
from .models import UploadHistory, DataSource, Country
from .tasks import update_achilles_results_data


VERSION_REGEX = regex.compile(r'\d+[\d.]*(?<!\.)')


def convert_to_datetime_from_iso(elem: str) -> Union[datetime.datetime, None]:
    """
    Function used to convert string dates received on the uploaded file.
    Used on the 'transform' argument of the function 'check_correct'.

    :param elem: string to convert to datetime
    :return: a datetime object or None if the string is not in a valid ISO format
    """
    analysis, stratum = elem

    try:
        return datetime.datetime.fromisoformat(analysis.loc[0, stratum])
    except ValueError:
        return None


# Type of the values received on the check_correct function
T = TypeVar("T")
# Type of the returned value from the transform callable argument of the check_correct function
U = TypeVar("U")


def check_correct(
        names: List[str],
        values: List[T],
        transform: Callable[[T], Union[U, None]],
        check: Callable[[U], bool],
) -> Union[List[U], str]:
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
        messages.error(
            request,
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
        achilles_results = achilles_results.astype({
            "analysis_id": numpy.int32,
            "count_value": numpy.int32,
        })
    except ValueError:
        messages.error(
            request,
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
        lambda e: not e.empty
    )

    if isinstance(output, str):
        messages.error(
            request,
            mark_safe(
                f"Analysis id{output} missing. Try (re)running the plugin "
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            ),
        )

        return

    return_value = {"achilles_results": achilles_results}

    analysis_0 = output[0].reset_index()
    analysis_5000 = output[1].reset_index()

    errors = []

    # check mandatory dates
    output = check_correct(
        [
            "Achilles generation date (analysis_id=0, stratum3)",
            "Source release date (analysis_id=5000, stratum_2)",
            "CDM release date (analysis_id=5000, stratum_3)",
        ],
        [(analysis_0, "stratum_3"), (analysis_5000, "stratum_2"), (analysis_5000, "stratum_3")],
        convert_to_datetime_from_iso,
        lambda date: date,
    )

    if isinstance(output, str):
        errors.append(f"The field{output} not in a ISO date format.")
    else:
        return_value["achilles_generation_date"] = output[0]
        return_value["source_release_date"] = output[1]
        return_value["cdm_release_date"] = output[2]

    # check mandatory versions
    output = check_correct(
        [
            "CDM version (analysis_id=0, stratum_1)",
            "Achilles version (analysis_id=5000, stratum_4)",
            "Vocabulary version (analysis_id=5000, stratum_5)",
        ],
        [(analysis_0, "stratum_2"), (analysis_5000, "stratum_4"), (analysis_5000, "stratum_5")],
        lambda elem: elem[0].loc[0, elem[1]],
        VERSION_REGEX.fullmatch,
    )

    if isinstance(output, str):
        errors.append(f"The field{output} not in a valid version format.")
    else:
        return_value["cdm_version"] = output[0]
        return_value["achilles_version"] = output[1]
        return_value["vocabulary_version"] = output[2]

    if errors:
        messages.error(request, mark_safe(
            " ".join(errors) + "<br/>Try (re)running the plugin "
            "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
            " on your database."
        ))
        return

    return return_value


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
            data = extract_data_from_uploaded_file(request)

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
                    achilles_version=data["achilles_version"],
                    achilles_generation_date=data["achilles_generation_date"],
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
                    obj_data_source.acronym
                )
                os.makedirs(data_source_storage_path, exist_ok=True)
                data["achilles_results"].to_csv(
                    os.path.join(
                        data_source_storage_path,
                        f"{len(upload_history)}.csv"
                    ),
                    index=False,
                )

                messages.success(
                    request,
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

        initial = {"acronym": data_source}

        if request.GET:  # if the request has arguments
            # compute fields' initial values
            for field_name, field in SourceForm.base_fields.items():
                if isinstance(field, fields.MultiValueField):
                    for i in range(len(field.widget.widgets)):
                        generated_field_name = f"{field_name}_{i}"
                        field_value = request.GET.get(generated_field_name)
                        if field_value:
                            initial[generated_field_name] = field_value
                elif field_name == "country":
                    countries_found = Country.objects.filter(country__icontains=request.GET["country"])
                    if countries_found.count() == 1:
                        initial["country"] = countries_found.get().id
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

            # since the form isn't valid, lets maintain only the valid fields
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

            form = SourceForm(initial=initial)

            # fill the form with errors associated with each field that wasn't valid
            #for field, msgs in aux_form.errors.items():
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
        if "acronym" not in request.POST and data_source is not None:
            request.POST["acronym"] = data_source

        form = SourceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            lat, lon = form.cleaned_data["coordinates"].split(",")
            obj.latitude, obj.longitude = float(lat), float(lon)
            obj.data_source = data_source
            obj.save()

            messages.success(
                request,
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
        }
    )
