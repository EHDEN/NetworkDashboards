
import datetime
from django.contrib import messages
from django.shortcuts import redirect, render, render_to_response
from django.utils.html import format_html, mark_safe
from django.http import HttpResponseRedirect

from .forms import SourceFrom, AchillesResultsForm
from .models import AchillesResults, UploadHistory, DataSource, AchillesResultsArchive


def upload_achilles_results(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    try:
        obj_data_source = DataSource.objects.get(slug=data_source)
    except DataSource.DoesNotExist:
        return create_data_source(request, *args, **kwargs)

    upload_history = list()
    if request.method == "GET":
        upload_history = list(
            UploadHistory
                .objects
                .filter(data_source__slug=obj_data_source.slug)
        )
        form = AchillesResultsForm()
    elif request.method == "POST":
        form = AchillesResultsForm(request.POST, request.FILES)
        if form.is_valid():
            uploads = UploadHistory.objects.filter(data_source__slug=obj_data_source.slug).order_by('-upload_date')

            error = None
            uploadedFile = request.FILES["achilles_results"]
            if uploadedFile.content_type == "text/csv":
                try:
                    is_header = form.cleaned_data["has_header"]
                    listOfEntries = []
                    for line in uploadedFile:
                        if not is_header:
                            listOfEntries.append(buildEntry(obj_data_source, line))
                        else:
                            is_header = False

                    insertIntoDB(listOfEntries)
                except IndexError:
                    error = "The csv file uploaded must have at least <b>seven</b> columns \
                        (analysis_id, stratum_1, stratum_2, stratum_3, stratum_4, stratum_5, count_value)."
            else:
                error = mark_safe("Uploaded achilles results files should be <b>CSV</b> files.")

            if not error:
                if len(uploads) > 0:
                    last_upload = uploads[0]

                    entries = []
                    for ach_res in AchillesResults.objects.filter(data_source=obj_data_source).all():
                        entries.append(
                            AchillesResultsArchive(
                                data_source=obj_data_source,
                                upload_info=last_upload,
                                analysis_id=ach_res.analysis_id,
                                stratum_1=ach_res.stratum_1,
                                stratum_2=ach_res.stratum_2,
                                stratum_3=ach_res.stratum_3,
                                stratum_4=ach_res.stratum_4,
                                stratum_5=ach_res.stratum_5,
                                count_value=ach_res.count_value
                            )
                        )
                    AchillesResultsArchive.objects.bulk_create(entries)
                    AchillesResults.objects.filter(data_source=obj_data_source).delete()


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

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Achilles Results file uploaded with success.",
                )
            
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


def create_data_source(request, *args, **kwargs):
    data_source = kwargs.get("data_source")
    if request.method == "GET":
        form = SourceFrom(initial={'slug': data_source})
        if data_source != None:
            form.fields["slug"].disabled = True
    elif request.method == "POST":
        if "slug" not in request.POST and data_source != None:
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


def buildEntry(db, line):
    #columns=("source","analysis_id","stratum_1","stratum_2","stratum_3","stratum_4","stratum_5","count_value")    
    newLine = line.decode('ASCII').strip().replace('"', "")
    newLine = [db] + newLine.split(",")
    return AchillesResults(data_source    = newLine[0],
                           analysis_id    = newLine[1],
                           stratum_1      = newLine[2],
                           stratum_2      = newLine[3],
                           stratum_3      = newLine[4],
                           stratum_4      = newLine[5],
                           stratum_5      = newLine[6],
                           count_value    = newLine[7])


def insertIntoDB(listOfEntries):
    AchillesResults.objects.bulk_create(listOfEntries)
