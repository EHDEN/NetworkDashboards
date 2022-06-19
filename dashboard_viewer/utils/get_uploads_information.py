from uploader.models import DataSource, UploadHistory

for db in DataSource.objects.all():
    print(f"{db.acronym},{db.name},{db.hash}", end="")
    try:
        last_upload = db.uploadhistory_set.latest()
    except UploadHistory.DoesNotExist:
        print()
    else:
        print(f",{last_upload.upload_date},{last_upload.generation_date}")
