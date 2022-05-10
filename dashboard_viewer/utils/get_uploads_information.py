from uploader.models import DataSource, UploadHistory
for db in DataSource.objects.all():
    try:
        last_upload = db.uploadhistory_set.latest()
    except UploadHistory.DoesNotExist:
        print("{},{},{}".format(db.acronym, db.name, db.hash))
    else:
        print("{},{},{},{},{}".format(db.acronym, db.name, db.hash, last_upload.upload_date, last_upload.generation_date))
