from django.shortcuts import render
from django.views.generic.edit import FormView
import pandas as pd
import sqlalchemy as sa
from django.conf import settings
from sqlalchemy import create_engine
from .models import AchillesResults



def upload(request, *args, **kwargs):
    if "db" not in kwargs:
        db = None
    else:
        db = kwargs["db"]
    success = False

    if request.method == 'POST':
        if db == None and 'inputDB' in request.POST:
            db = request.POST['inputDB']

        if db != None:
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

    context = {
        "db": db,
        "success": success
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