import pandas
from django.db import connections

from uploader.models import (
    AchillesResults,
    AchillesResultsArchive,
    DataSource,
    PendingUpload,
    UploadHistory,
)


def update_achilles_results_data(
    logger,
    pending_upload: PendingUpload,
    file_metadata,
    pandas_connection,
):
    data_source_id = pending_upload.data_source.id

    logger.info(
        "Moving old records to the AchillesResultsArchive table [datasource %d, pending upload %d]",
        data_source_id,
        pending_upload.id,
    )
    with connections["achilles"].cursor() as cursor:
        move_achilles_results_records(
            cursor,
            AchillesResults,
            AchillesResultsArchive,
            data_source_id,
        )

    reader = pandas.read_csv(
        pending_upload.uploaded_file,
        header=0,
        dtype=file_metadata["types"],
        skip_blank_lines=False,
        index_col=False,
        names=file_metadata["columns"],
        chunksize=500,
    )

    logger.info(
        "Inserting new results records [datasource %d, pending upload %d]",
        data_source_id,
        pending_upload.id,
    )

    for chunk in reader:
        chunk = chunk.assign(data_source_id=data_source_id)
        chunk.to_sql(
            AchillesResults._meta.db_table,
            pandas_connection,
            if_exists="append",
            index=False,
        )


def move_achilles_results_records(
    cursor, origin_model, destination_model, db_id, last_upload_id=None
):
    allowed_models = (AchillesResults, AchillesResultsArchive)

    if origin_model not in allowed_models or destination_model not in allowed_models:
        raise ValueError(
            f"The only allowed models are {''.join(model.__name__ for model in allowed_models)}"
        )
    if origin_model == AchillesResultsArchive:
        raise ValueError(
            "AchillesResultsArchive can only be used as a destination model"
        )
    if origin_model == destination_model:
        raise ValueError("Origin and destination models can't be the same")
    if not DataSource.objects.filter(id=db_id).exists():
        raise ValueError("No datasource with the provided id")

    if last_upload_id is None:
        try:
            last_upload_id = (
                UploadHistory.objects.filter(data_source_id=db_id).latest().id
            )
        except UploadHistory.DoesNotExist:
            return  # nothing to move
    elif not UploadHistory.objects.filter(
        id=last_upload_id, data_source_id=db_id
    ).exists():
        raise ValueError("There is no UploadHistory with the provided id")

    cursor.execute(
        f"""
        INSERT INTO {destination_model._meta.db_table} (
            {destination_model.analysis_id.field.name},
            {destination_model.stratum_1.field.name},
            {destination_model.stratum_2.field.name},
            {destination_model.stratum_3.field.name},
            {destination_model.stratum_4.field.name},
            {destination_model.stratum_5.field.name},
            {destination_model.count_value.field.name},
            {destination_model.min_value.field.name},
            {destination_model.max_value.field.name},
            {destination_model.avg_value.field.name},
            {destination_model.stdev_value.field.name},
            {destination_model.median_value.field.name},
            {destination_model.p10_value.field.name},
            {destination_model.p25_value.field.name},
            {destination_model.p75_value.field.name},
            {destination_model.p90_value.field.name},
            {destination_model.data_source.field.column},
            {destination_model.upload_info.field.column}
        )
        SELECT
            {origin_model.analysis_id.field.name},
            {origin_model.stratum_1.field.name},
            {origin_model.stratum_2.field.name},
            {origin_model.stratum_3.field.name},
            {origin_model.stratum_4.field.name},
            {origin_model.stratum_5.field.name},
            {origin_model.count_value.field.name},
            {origin_model.min_value.field.name},
            {origin_model.max_value.field.name},
            {origin_model.avg_value.field.name},
            {origin_model.stdev_value.field.name},
            {origin_model.median_value.field.name},
            {origin_model.p10_value.field.name},
            {origin_model.p25_value.field.name},
            {origin_model.p75_value.field.name},
            {origin_model.p90_value.field.name},
            {origin_model.data_source.field.column},
            %s
        FROM {origin_model._meta.db_table}
        WHERE {origin_model.data_source.field.column} = %s
        """,
        (last_upload_id, db_id),
    )

    origin_model.objects.filter(data_source_id=db_id).delete()
