from __future__ import absolute_import, unicode_literals

from contextlib import closing
from typing import Union

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.conf import settings
from django.db import connections
from redis_rw_lock import RWLock
import pandas

from .models import AchillesResults, AchillesResultsArchive
from materialized_queries_manager.models import MaterializedQuery

logger = get_task_logger(__name__)


@shared_task
def update_achilles_results_data(
    db_id: int, last_upload_id: Union[int, None], achilles_results: str
) -> None:
    logger.info(f"Worker started [datasource {db_id}]")
    cache.incr("celery_workers_updating", ignore_key_check=True)

    # several workers can update records concurrently -> same as -> several threads can read from the same file
    read_lock = RWLock(cache.client.get_client(), "celery_worker_updating", RWLock.READ)
    read_lock.acquire()

    # but only one worker can make updates associated to a specific data source at the same time
    with cache.lock(f"celery_worker_lock_db_{db_id}"):
        logger.info(f"Updating achilles results records [datasource {db_id}]")

        entries = pandas.read_json(achilles_results)

        if last_upload_id:
            # if there were any records uploaded before
            #  move them to the AchillesResultsArchive table
            logger.info(
                f"Moving old records to the {AchillesResultsArchive._meta.db_table} table [datasource {db_id}]"
            )
            with closing(connections["achilles"].cursor()) as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {AchillesResultsArchive._meta.db_table} (
                        {AchillesResultsArchive.analysis_id.field_name},
                        {AchillesResultsArchive.stratum_1.field_name},
                        {AchillesResultsArchive.stratum_2.field_name},
                        {AchillesResultsArchive.stratum_3.field_name},
                        {AchillesResultsArchive.stratum_4.field_name},
                        {AchillesResultsArchive.stratum_5.field_name},
                        {AchillesResultsArchive.count_value.field_name},
                        {AchillesResultsArchive.data_source.field.column},
                        {AchillesResultsArchive.upload_info.field.column}
                    )
                    SELECT
                        {AchillesResults.analysis_id.field_name},
                        {AchillesResults.stratum_1.field_name},
                        {AchillesResults.stratum_2.field_name},
                        {AchillesResults.stratum_3.field_name},
                        {AchillesResults.stratum_4.field_name},
                        {AchillesResults.stratum_5.field_name},
                        {AchillesResults.count_value.field_name},
                        %s, %s
                    FROM {AchillesResults._meta.db_table}
                    """,
                    (db_id, last_upload_id),
                )

            logger.info(
                f"Deleting old records from {AchillesResults._meta.db_table} table [datasource {db_id}]"
            )
            AchillesResults.objects.filter(data_source_id=db_id).delete()

        entries["data_source_id"] = db_id

        logger.info(
            f"Inserting new records on {AchillesResults._meta.db_table} table [datasource {db_id}]"
        )
        entries.to_sql(
            AchillesResults._meta.db_table,
            "postgresql"  # TODO aspedrosa: this shouldn't be hardcoded
            f"://{settings.DATABASES['achilles']['USER']}:{settings.DATABASES['achilles']['PASSWORD']}"
            f"@{settings.DATABASES['achilles']['HOST']}:{settings.DATABASES['achilles']['PORT']}"
            f"/{settings.DATABASES['achilles']['NAME']}",
            if_exists="append",
            index=False,
        )

    read_lock.release()

    # The lines below can be used to later update materialized views of each chart
    # To be more efficient, they should only be updated when the is no more workers inserting records
    if not cache.decr("celery_workers_updating"):
        # Only one worker can update the materialized views at the same time -> same as -> only one thread
        #  can write to a file at the same time
        write_lock = RWLock(
            cache.client.get_client(), "celery_worker_updating", RWLock.WRITE
        )
        write_lock.acquire()

        logger.info(f"Updating materialized views [datasource {db_id}]")
        with closing(connections["achilles"].cursor()) as cursor:
            for materialized_query in MaterializedQuery.objects.all():
                cursor.execute(f"REFRESH MATERIALIZED VIEW {materialized_query.name}")

        write_lock.release()

    logger.info(f"Done [datasource {db_id}]")
