from __future__ import absolute_import, unicode_literals

from contextlib import closing
from typing import Union

import pandas
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.db import connections, ProgrammingError
from materialized_queries_manager.models import MaterializedQuery
from redis_rw_lock import RWLock

from .models import AchillesResults, AchillesResultsArchive

logger = get_task_logger(__name__)


@shared_task
def update_achilles_results_data(
    db_id: int, last_upload_id: Union[int, None], achilles_results: str
) -> None:
    logger.info("Worker started [datasource %d]", db_id)
    cache.incr("celery_workers_updating", ignore_key_check=True)

    # several workers can update records concurrently -> same as -> several threads can read from the same file
    read_lock = RWLock(cache.client.get_client(), "celery_worker_updating", RWLock.READ)
    read_lock.acquire()

    # but only one worker can make updates associated to a specific data source at the same time
    with cache.lock(f"celery_worker_lock_db_{db_id}"):
        logger.info("Updating achilles results records [datasource %d]", db_id)

        entries = pandas.read_json(achilles_results)

        if last_upload_id:
            # if there were any records uploaded before
            #  move them to the AchillesResultsArchive table
            logger.info(
                "Moving old records to the %s table [datasource %d]",
                AchillesResultsArchive._meta.db_table,
                db_id,
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
                        {AchillesResultsArchive.min_value.field_name},
                        {AchillesResultsArchive.max_value.field_name},
                        {AchillesResultsArchive.avg_value.field_name},
                        {AchillesResultsArchive.stdev_value.field_name},
                        {AchillesResultsArchive.median_value.field_name},
                        {AchillesResultsArchive.p10_value.field_name},
                        {AchillesResultsArchive.p25_value.field_name},
                        {AchillesResultsArchive.p75_value.field_name},
                        {AchillesResultsArchive.p90_value.field_name},
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
                        {AchillesResults.min_value.field_name},
                        {AchillesResults.max_value.field_name},
                        {AchillesResults.avg_value.field_name},
                        {AchillesResults.stdev_value.field_name},
                        {AchillesResults.median_value.field_name},
                        {AchillesResults.p10_value.field_name},
                        {AchillesResults.p25_value.field_name},
                        {AchillesResults.p75_value.field_name},
                        {AchillesResults.p90_value.field_name},
                        %s, %s
                    FROM {AchillesResults._meta.db_table}
                    """,
                    (db_id, last_upload_id),
                )

            logger.info(
                "Deleting old records from %s table [datasource %d]",
                AchillesResults._meta.db_table,
                db_id,
            )
            AchillesResults.objects.filter(data_source_id=db_id).delete()

        entries["data_source_id"] = db_id

        logger.info(
            "Inserting new records on %s table [datasource %d]",
            AchillesResults._meta.db_table,
            db_id,
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

        logger.info("Updating materialized views [datasource %d]", db_id)
        with closing(connections["achilles"].cursor()) as cursor:
            for materialized_query in MaterializedQuery.objects.all():
                try:
                    cursor.execute(
                        f"REFRESH MATERIALIZED VIEW {materialized_query.name}"
                    )
                except ProgrammingError:
                    # If this happen, it is assumed its because the there is no materialized views
                    #  created on postgres with the given name
                    # TODO Log this or give some feed back on the Materialized query list, on admin app, if any
                    #  record doesn't have a materialized view associated.
                    pass  # Ignore if the view doesn't exist
                except:  # noqa
                    logger.exception(
                        "Some unexpected error happen while refreshing materialized query %s. [datasource %d]",
                        materialized_query.name,
                        db_id,
                    )

        write_lock.release()

    logger.info("Done [datasource %d]", db_id)
