#!/bin/sh

set -x

# clean locks
echo '''from django.core.cache import caches
cache = caches["workers_locks"]
cache.delete_pattern("*")
''' | python manage.py shell

# remove all pending tasks
celery -A dashboard_viewer purge -f

# start unfinished pending uploads
echo '''from django.db.models import Q
from uploader.models import PendingUpload
from uploader.tasks import upload_results_file
for pu in PendingUpload.objects.filter(Q(status=PendingUpload.STATE_PENDING) | Q(status=PendingUpload.STATE_STARTED)):
    print(f"Starting {pu.id}")
    upload_results_file.delay(pu.id)
''' | python manage.py shell

# 4. start celery
exec celery -A dashboard_viewer worker -Ofair -l INFO
