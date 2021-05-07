from __future__ import absolute_import, unicode_literals

from typing import Union

import pandas
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.db import connections, router, transaction
from redis_rw_lock import RWLock

from materialized_queries_manager.utils import refresh
from .models import (
    AchillesResults,
    AchillesResultsArchive,
    AchillesResultsDraft,
    DataSource,
)
from .utils import move_achilles_results_records

logger = get_task_logger(__name__)


@shared_task
def update_achilles_results_data(
        db_id: int, last_upload_id: Union[int, None], achilles_results: str
) -> None:
    logger.info("Worker started [datasource %d]", db_id)
    cache.incr("celery_workers_updating", ignore_key_check=True)

    # several workers can update records concurrently -> same as -> several threads can read from the same file
    with RWLock(
            cache.client.get_client(), "celery_worker_updating", RWLock.READ, expire=None
    ):
        store_table = (
            AchillesResultsDraft
            if DataSource.objects.get(id=db_id).draft
            else AchillesResults
        )

        # but only one worker can make updates associated to a specific data source at the same time
        with transaction.atomic(using=router.db_for_write(store_table)), cache.lock(
                f"celery_worker_lock_db_{db_id}"
        ):
            logger.info("Updating achilles results records [datasource %d]", db_id)

            logger.info(
                "Moving old records to the %s table [datasource %d]",
                AchillesResultsArchive._meta.db_table,
                db_id,
            )
            with connections["achilles"].cursor() as cursor:
                move_achilles_results_records(
                    cursor, store_table, AchillesResultsArchive, db_id, last_upload_id
                )

            entries = pandas.read_json(achilles_results)
            entries["data_source_id"] = db_id

            logger.info(
                "Inserting new records on %s table [datasource %d]",
                store_table._meta.db_table,
                db_id,
            )
            entries.to_sql(
                store_table._meta.db_table,
                "postgresql"
                f"://{settings.DATABASES['achilles']['USER']}:{settings.DATABASES['achilles']['PASSWORD']}"
                f"@{settings.DATABASES['achilles']['HOST']}:{settings.DATABASES['achilles']['PORT']}"
                f"/{settings.DATABASES['achilles']['NAME']}",
                if_exists="append",
                index=False,
            )

    # The lines below can be used to later update materialized views of each chart
    # To be more efficient, they should only be updated when the is no more workers inserting records
    if not cache.decr("celery_workers_updating"):
        refresh(logger, db_id)

    logger.info("Done [datasource %d]", db_id)


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
