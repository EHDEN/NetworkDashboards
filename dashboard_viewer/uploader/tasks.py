
from __future__ import absolute_import, unicode_literals

from contextlib import closing

from celery import shared_task
from django.core.serializers import deserialize
from django.db import connections

from uploader.models import AchillesResults


@shared_task
def update_achilles_results_data(serialized_args, entries):
    serialized_args = list(deserialize('json', serialized_args))

    db = serialized_args[0].object
    last_upload = serialized_args[1].object

    if last_upload:
        with closing(connections["achilles"].cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO achilles_results_archive (analysis_id, stratum_1, stratum_2, stratum_3, stratum_4, stratum_5, count_value, data_source_id, upload_info_id)
                SELECT analysis_id, stratum_1, stratum_2, stratum_3, stratum_4, stratum_5, count_value, %s, %s
                FROM achilles_results
                """,
                (db.id, last_upload.id)
            )
        AchillesResults.objects.filter(data_source=db).delete()

    max_write_chunk = 100000

    count = 0
    to_insert = [None] * max_write_chunk
    for entry in entries:
        to_insert[count] = AchillesResults(
            data_source=db,
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

