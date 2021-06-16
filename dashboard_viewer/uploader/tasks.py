from celery import shared_task
from celery.utils.log import get_task_logger
from django.core import serializers
from django.core.cache import cache
from django.db import router, transaction

from materialized_queries_manager.utils import refresh
from redis_rw_lock import RWLock

from .models import (
    AchillesResults,
    UploadHistory,
    PendingUpload,
)

from .file_handler.checks import extract_data_from_uploaded_file
from .file_handler.updates import update_achilles_results_data

logger = get_task_logger(__name__)


@shared_task
def upload_results_file(pending_upload_id: int):
    pending_upload = PendingUpload.objects.get(id=pending_upload_id)

    pending_upload.status = PendingUpload.STATE_STARTED
    pending_upload.save()

    try:
        file_metadata, data = extract_data_from_uploaded_file(pending_upload.uploaded_file)
    except Exception as e:
        pending_upload.status = PendingUpload.STATE_FAILED
        pending_upload.save()

        raise e

    data_source = pending_upload.data_source

    cache.incr("celery_workers_updating", ignore_key_check=True)

    with RWLock(  # several workers can update their records in paralel -> same as -> several threads can read from the same file
        cache.client.get_client(), "celery_worker_updating", RWLock.READ, expire=None
    ), cache.lock(  # but only one worker can make updates associated to a specific data source at the same time
        f"celery_worker_lock_db_{data_source.id}"
    ), transaction.atomic(using=router.db_for_write(AchillesResults)):
        pending_upload.uploaded_file.seek(0)
        update_achilles_results_data(pending_upload, file_metadata)

        data_source.release_date = data["source_release_date"]
        data_source.save()

        pending_upload.uploaded_file.seek(0)
        UploadHistory.objects.create(
            data_source=data_source,
            r_package_version=data["r_package_version"],
            generation_date=data["generation_date"],
            cdm_release_date=data["cdm_release_date"],
            cdm_version=data["cdm_version"],
            vocabulary_version=data["vocabulary_version"],
            uploaded_file=pending_upload.uploaded_file.file,
        )

        pending_upload.uploaded_file.delete()
        pending_upload.delete()

    # The lines below can be used to later update materialized views of each chart
    # To be more efficient, they should only be updated when the is no more workers inserting records
    if not cache.decr("celery_workers_updating"):
        refresh(logger, data_source.id)


@shared_task
def delete_datasource(objs):
    cache.incr("celery_workers_updating", ignore_key_check=True)

    read_lock = RWLock(
        cache.client.get_client(), "celery_worker_updating", RWLock.READ, expire=None
    )
    read_lock.acquire()

    objs = serializers.deserialize("json", objs)

    for obj in objs:
        obj = obj.object
        with cache.lock(f"celery_worker_lock_db_{obj.pk}"):
            obj.delete()

    read_lock.release()

    if not cache.decr("celery_workers_updating"):
        refresh(logger)
