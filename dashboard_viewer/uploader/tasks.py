
from __future__ import absolute_import, unicode_literals

from contextlib import closing

from celery import shared_task
from django.core.cache import cache
from django.db import connections
from redis_rw_lock import RWLock

from .models import AchillesResults, AchillesResultsArchive


@shared_task
def update_achilles_results_data(db_id, last_upload_id, entries):
    cache.incr("celery_workers_updating", ignore_key_check=True)

    # several workers can update records concurrently -> same as -> several threads can read from the same file
    read_lock = RWLock(cache.client.get_client(), "celery_worker_updating", RWLock.READ)
    read_lock.acquire()

    # but only one worker can make updates associated to a specific data source at the same time
    with cache.lock(f"celery_worker_lock_db_{db_id}"):
        if last_upload_id:
            # if there were any records uploaded before
            #  move them to the AchillesResultsArchive table
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
                    (db_id, last_upload_id)
                )

            # delete moved records
            AchillesResults.objects.filter(data_source_id=db_id).delete()

        # insert the new records
        max_write_chunk = 100000

        count = 0
        to_insert = [None] * max_write_chunk
        for entry in entries:
            to_insert[count] = AchillesResults(
                data_source_id=db_id,
                analysis_id=entry[0],
                stratum_1  =entry[1],
                stratum_2  =entry[2],
                stratum_3  =entry[3],
                stratum_4  =entry[4],
                stratum_5  =entry[5],
                count_value=entry[6]
            )

            count += 1

            if count == max_write_chunk:
                AchillesResults.objects.bulk_create(to_insert)
                count = 0

        if count > 0:
            AchillesResults.objects.bulk_create(to_insert[:count])

    read_lock.release()

    # The lines below can be used to later update materialized views of each chart
    # To be more efficient, they should only be updated when the is no more workers inserting records
    if not cache.decr("celery_workers_updating", ignore_key_check=True):
        # Only one worker can update the materialized views at the same time -> same as -> only one thread
        #  can write to a file at the same time
        write_lock = RWLock(cache.client.get_client(), "celery_worker_updating", RWLock.WRITE)
        write_lock.acquire()

        # TODO update materialized view

        write_lock.release()
