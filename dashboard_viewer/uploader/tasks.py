from celery import shared_task
from celery.utils.log import get_task_logger
from django.core import serializers
from django.core.cache import cache
from django.db import router, transaction
from redis_rw_lock import RWLock

from materialized_queries_manager.utils import refresh
from .file_handler.checks import (
    check_for_duplicated_files,
    extract_data_from_uploaded_file,
)
from .file_handler.updates import update_achilles_results_data
from .models import AchillesResults, PendingUpload, UploadHistory

logger = get_task_logger(__name__)


@shared_task
def upload_results_file(pending_upload_id: int):
    pending_upload = PendingUpload.objects.get(id=pending_upload_id)

    pending_upload.status = PendingUpload.STATE_STARTED
    pending_upload.save()

    data_source = pending_upload.data_source

    logger.info(
        "Started to process file [datasource %d, pending upload %d]",
        data_source.id,
        pending_upload_id,
    )

    try:
        # To prevent the database owner from uploading the same data to the datasource

        logger.info(
            "Verifying Checksum of the upload file with recent data [datasource %d, pending upload %d]",
            data_source.id,
            pending_upload.id,
        )

        check_for_duplicated_files(pending_upload.uploaded_file, data_source.id)

        logger.info(
            "Checking file format and data [datasource %d, pending upload %d]",
            data_source.id,
            pending_upload_id,
        )
        file_metadata, data = extract_data_from_uploaded_file(
            pending_upload.uploaded_file
        )

        try:
            cache.incr("celery_workers_updating", ignore_key_check=True)

            with RWLock(  # several workers can update their records in paralel -> same as -> several threads can read from the same file
                cache.client.get_client(),
                "celery_worker_updating",
                RWLock.READ,
                expire=None,
            ), cache.lock(  # but only one worker can make updates associated to a specific data source at the same time
                f"celery_worker_lock_db_{data_source.id}"
            ), transaction.atomic(
                using=router.db_for_write(AchillesResults)
            ):
                logger.info(
                    "Updating results data [datasource %d, pending upload %d]",
                    data_source.id,
                    pending_upload_id,
                )

                pending_upload.uploaded_file.seek(0)
                update_achilles_results_data(logger, pending_upload, file_metadata)

                logger.info(
                    "Creating an upload history record [datasource %d, pending upload %d]",
                    data_source.id,
                    pending_upload_id,
                )

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
                    pending_upload_id=pending_upload.id,
                )

                pending_upload.uploaded_file.delete()
                pending_upload.delete()
        finally:
            workers_updating = cache.decr("celery_workers_updating")
    except Exception as e:
        pending_upload.status = PendingUpload.STATE_FAILED
        pending_upload.save()

        raise e

    # The lines below can be used to later update materialized views of each chart
    # To be more efficient, they should only be updated when the is no more workers inserting records
    if not workers_updating:
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
