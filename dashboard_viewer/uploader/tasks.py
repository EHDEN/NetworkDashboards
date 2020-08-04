
from __future__ import absolute_import, unicode_literals

from contextlib import closing

from celery import shared_task
from django.db import connections

from .models import AchillesResults, AchillesResultsArchive


@shared_task
def update_achilles_results_data(db_id, last_upload_id, entries):
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
        AchillesResults.objects.filter(data_source_id=db_id).delete()

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
