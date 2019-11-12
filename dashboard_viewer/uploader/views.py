from django.shortcuts import render
from django.views.generic.edit import FormView
import pandas as pd
import sqlalchemy as sa
from django.conf import settings
from sqlalchemy import create_engine


def upload(request, *args, **kwargs):
    if request.method == 'POST':
        if "db" not in kwargs:
            pass #raise issue
        db = kwargs["db"]
        uploadedFile = request.FILES["achillesResults"]
        if uploadedFile.content_type == "text/csv":
            READ = False
            fileContent = []
            for line in uploadedFile:
                if READ:
                    newLine = line.decode('ASCII').strip().replace('"', "")
                    newLine = [db] + newLine.split(",")
                    fileContent += [newLine]
                else:
                    READ = True
            df = pd.DataFrame(fileContent, columns=("source","analysis_id","stratum_1","stratum_2","stratum_3","stratum_4","stratum_5","count_value"))
            insertIntoDB(df)
    return render(request, 'upload.html')

def insertIntoDB(df):
    engine = create_engine("postgresql://"+
                           settings.DATABASES['default']['USER']+":"+settings.DATABASES['default']['PASSWORD']+"@"+
                           settings.DATABASES['default']['HOST']+":"+settings.DATABASES['default']['PORT']+"/"+
                           settings.DATABASES['default']['NAME'])

    dtype = {
        "source":       sa.types.String,
        "analysis_id":  sa.types.BigInteger,
        "stratum_1":    sa.types.String,
        "stratum_2":    sa.types.String,
        "stratum_3":    sa.types.String,
        "stratum_4":    sa.types.String,
        "stratum_5":    sa.types.String,
        "count_value":  sa.types.BigInteger
    }
    df.to_sql("achilles_results", engine,   if_exists  = 'append',
                                            index      = False,
                                            schema     = "public",
                                            dtype      = dtype)
   