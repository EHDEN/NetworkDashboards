from .models import (
    AchillesResults,
    AchillesResultsArchive,
    DataSource,
    UploadHistory,
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

    if destination_model == AchillesResultsArchive:
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

        upload_info_column = f", {destination_model.upload_info.field.column}"
        upload_info_value = ", %s"
        query_args = (last_upload_id, db_id)
    else:
        upload_info_column = ""
        upload_info_value = ""
        query_args = (db_id,)

    cursor.execute(
        f"""
        INSERT INTO {destination_model._meta.db_table} (
            {destination_model.analysis_id.field_name},
            {destination_model.stratum_1.field_name},
            {destination_model.stratum_2.field_name},
            {destination_model.stratum_3.field_name},
            {destination_model.stratum_4.field_name},
            {destination_model.stratum_5.field_name},
            {destination_model.count_value.field_name},
            {destination_model.min_value.field_name},
            {destination_model.max_value.field_name},
            {destination_model.avg_value.field_name},
            {destination_model.stdev_value.field_name},
            {destination_model.median_value.field_name},
            {destination_model.p10_value.field_name},
            {destination_model.p25_value.field_name},
            {destination_model.p75_value.field_name},
            {destination_model.p90_value.field_name},
            {destination_model.data_source.field.column}
            {upload_info_column}
        )
        SELECT
            {origin_model.analysis_id.field_name},
            {origin_model.stratum_1.field_name},
            {origin_model.stratum_2.field_name},
            {origin_model.stratum_3.field_name},
            {origin_model.stratum_4.field_name},
            {origin_model.stratum_5.field_name},
            {origin_model.count_value.field_name},
            {origin_model.min_value.field_name},
            {origin_model.max_value.field_name},
            {origin_model.avg_value.field_name},
            {origin_model.stdev_value.field_name},
            {origin_model.median_value.field_name},
            {origin_model.p10_value.field_name},
            {origin_model.p25_value.field_name},
            {origin_model.p75_value.field_name},
            {origin_model.p90_value.field_name},
            {origin_model.data_source.field.column}
            {upload_info_value}
        FROM {origin_model._meta.db_table}
        WHERE {origin_model.data_source.field.column} = %s
        """,
        query_args,
    )

    origin_model.objects.filter(data_source_id=db_id).delete()
