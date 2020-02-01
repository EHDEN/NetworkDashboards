
from django.shortcuts import render

from .models import AchillesResults, UploadHistory, Sources, DatabaseType
from .forms import SourceFrom, AchillesResultsForm


def upload(request, *args, **kwargs):
    db = kwargs.get("db")

    if request.method == "GET":
        if db is None:
            form = SourceFrom(DatabaseType.objects.all())
        else:
            if Sources.objects.filter(name=db).count() == 0:
                return render(
                    request,
                    "upload.html",
                    {
                        "form": SourceFrom(DatabaseType.objects.all()),
                        "found_db": False
                    }
                )  # TODO send alert on html

            form = AchillesResultsForm()
    elif request.method == "POST":
        if db is None:
            form = SourceFrom(request.POST)
            if form.is_valid():
                form.save()
                form = AchillesResultsForm()
        else:
            form = AchillesResultsForm(request.POST)
            if form.is_valid():
                uploads = UploadHistory.objects.filter(Source__name=db).order_by("-date")

                form.cleaned_data[""]

                pass  # TODO to make a new upload

    """
    if request.method == 'POST':
        if db is None and 'inputDB' in request.POST:
            db = request.POST['inputDB']

        if db is not None:
            uploadedFile = request.FILES["achillesResults"]
            if uploadedFile.content_type == "text/csv":
                READ = False
                listOfEntries = []
                for line in uploadedFile:
                    if READ:
                        listOfEntries.append(buildEntry(db, line))
                    else:
                        READ = True

                insertIntoDB(listOfEntries, db)
        success = True
        """

    context = {
        "form": form,
        "found_db": True,
    }
    return render(request, 'upload.html', context)


def buildEntry(db, line):
    #columns=("source","analysis_id","stratum_1","stratum_2","stratum_3","stratum_4","stratum_5","count_value")    
    newLine = line.decode('ASCII').strip().replace('"', "")
    newLine = [db] + newLine.split(",")
    return AchillesResults(source         = newLine[0],
                           analysis_id    = newLine[1],
                           stratum_1      = newLine[2],
                           stratum_2      = newLine[3],
                           stratum_3      = newLine[4],
                           stratum_4      = newLine[5],
                           stratum_5      = newLine[6],
                           count_value    = newLine[7])


def insertIntoDB(listOfEntries, database):
    AchillesResults.objects.bulk_create(listOfEntries)
