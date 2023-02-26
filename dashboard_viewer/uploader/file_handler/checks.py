import csv
import hashlib
import io
import os

import numpy
import pandas
from django.conf import settings
from django.core.cache import caches
from django.db import connections, transaction, utils
from redis_rw_lock import RWLock

from materialized_queries_manager.models import MaterializedQuery
from uploader.models import AchillesResults, DataSource, UploadHistory


class FileChecksException(Exception):
    pass


class InvalidCSVFile(FileChecksException):
    pass


class InvalidFileFormat(FileChecksException):
    pass


class InvalidFieldValue(FileChecksException):
    pass


class DuplicatedMetadataRow(FileChecksException):
    pass


class MissingFieldValue(FileChecksException):
    pass


class EqualFileAlreadyUploaded(FileChecksException):
    pass


class FileDataCorrupted(FileChecksException):
    pass


def _generate_file_reader(uploaded_file):
    """
    Receives a python file pointer and returns a pandas csv file reader, along with the columns
     present in the file
    :param uploaded_file: python file pointer of the uploaded file
    """
    columns = [
        "analysis_id",
        "stratum_1",
        "stratum_2",
        "stratum_3",
        "stratum_4",
        "stratum_5",
        "count_value",
    ]

    wrapper = io.TextIOWrapper(uploaded_file)
    csv_reader = csv.reader(wrapper)

    try:
        first_row = next(csv_reader)
    except:  # noqa
        raise InvalidCSVFile(
            "There was an error parsing the provided file. "
            "Uploaded files must be comma-separated values (CSV) files. "
            "If you think this is an error, please contact the system administrator."
        )

    wrapper.detach()

    if len(first_row) == 16:
        columns.extend(
            (
                "min_value",
                "max_value",
                "avg_value",
                "stdev_value",
                "median_value",
                "p10_value",
                "p25_value",
                "p75_value",
                "p90_value",
            )
        )
    elif len(first_row) != 7:
        raise InvalidFileFormat(
            "The provided file has an invalid number of columns. "
            "Make sure you uploaded a valid comma-separated values (CSV) file."
        )

    uploaded_file.seek(0)

    try:  # noqa
        file_reader = pandas.read_csv(
            uploaded_file,
            header=0,
            dtype=str,
            skip_blank_lines=False,
            index_col=False,
            names=columns,
            chunksize=100,
        )
    except:  # noqa
        raise InvalidCSVFile(
            "There was an error parsing the provided file. "
            "Uploaded files must be comma-separated values (CSV) files. "
            "If you think this is an error, please contact the system administrator."
        )
    else:
        return file_reader, columns


def _check_correct(names, values, check, transform=None):
    """
    Transforms the values of given fields from the uploaded file
     and check if they end up in the desired format

    :param names: names of the fields to check
    :param values: values of the fields to transform and check if they are
     in the right format
    :param transform: callable to transform the values of the
     provided fields
    :param check: callable check if the transform processes generated
     a valid output
    :return: the transformed fields or an error string
    """
    assert len(names) == len(values)

    transformed_elements = [None] * len(names)
    bad_elements = []

    for i, name in enumerate(names):
        transformed = values[i] if not transform else transform(values[i])
        if not check(transformed):
            bad_elements.append(name)
        else:
            transformed_elements[i] = transformed

    if bad_elements:
        return (
            f" {bad_elements[0]} is"
            if len(bad_elements) == 1
            else f"s {', '.join(bad_elements[:-1])} and {bad_elements[-1]} are"
        )

    return transformed_elements


def extract_data_from_uploaded_file(uploaded_file):
    file_reader, columns = _generate_file_reader(uploaded_file)

    types = {
        "analysis_id": numpy.int64,
        "stratum_1": "string",
        "stratum_2": "string",
        "stratum_3": "string",
        "stratum_4": "string",
        "stratum_5": "string",
        "count_value": numpy.int64,
    }
    if len(columns) == 16:
        types.update(
            {
                "min_value": float,
                "max_value": float,
                "avg_value": float,
                "stdev_value": float,
                "median_value": float,
                "p10_value": float,
                "p25_value": float,
                "p75_value": float,
                "p90_value": float,
            },
        )

    metadata = None

    while True:
        try:
            chunk = next(file_reader)
        except ValueError:
            raise InvalidFileFormat(
                "The provided file has an invalid csv format. Make sure is a text file separated"
                " by <b>commas</b> and you either have 7 (regular results file) or 13 (results file"
                " with dist columns) columns."
            )
        except StopIteration:
            break
        except:  # noqa
            raise InvalidCSVFile(
                "There was an error parsing the provided file. "
                "Uploaded files must be comma-separated values (CSV) files. "
                "If you think this is an error, please contact the system administrator."
            )

        if chunk[["analysis_id", "count_value"]].isna().values.any():
            raise InvalidFieldValue(
                'Some rows have null values either on the column "analysis_id" or "count_value".'
            )

        try:
            chunk = chunk.astype(types)
        except ValueError:
            raise InvalidFieldValue(
                'The provided file has invalid values on some columns. Remember that only the "stratum_*" columns'
                " accept strings, all the other fields expect numeric types."
            )

        metadata_rows = chunk[chunk.analysis_id.isin((0, 5000))]

        if metadata is None:
            metadata = metadata_rows
        else:
            metadata = pandas.concat(
                (metadata, metadata_rows), ignore_index=True, copy=False
            )

        output = _check_correct(
            ["0", "5000"],
            (
                metadata[metadata.analysis_id == 0],
                metadata[metadata.analysis_id == 5000],
            ),
            lambda e: len(e) <= 1,
        )
        if isinstance(output, str):
            raise DuplicatedMetadataRow(
                f"Analysis id{output} duplicated on multiple rows. Try (re)running the plugin "
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            )

    analysis_0 = metadata[metadata.analysis_id == 0]
    if analysis_0.empty:
        raise MissingFieldValue(
            "Analysis id 0 is missing. Try (re)running the plugin "
            "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
            " on your database."
        )

    analysis_0 = analysis_0.reset_index()
    analysis_5000 = metadata[metadata.analysis_id == 5000].reset_index()

    return {"columns": columns, "types": types}, {
        "generation_date": _get_upload_attr(analysis_0, "stratum_3"),
        "source_release_date": _get_upload_attr(analysis_5000, "stratum_2"),
        "cdm_release_date": _get_upload_attr(analysis_5000, "stratum_3"),
        "cdm_version": _get_upload_attr(analysis_5000, "stratum_4"),
        "r_package_version": _get_upload_attr(analysis_0, "stratum_2"),
        "vocabulary_version": _get_upload_attr(analysis_5000, "stratum_5"),
    }


def _get_upload_attr(analysis, stratum):
    if analysis.empty:
        return None

    value = analysis.loc[0, stratum]

    if pandas.isna(value):
        return None
    return value


def check_for_duplicated_files(uploaded_file, data_source_id):
    #### Added For Checksum ##########################

    try:
        # Upload History only stores the succesded files

        pd = UploadHistory.objects.filter(data_source_id=data_source_id).latest()

        data_source_hash = (
            DataSource.objects.filter(id=data_source_id)
            .values_list("hash", flat=True)
            .first()
        )

        if data_source_hash is not None:
            # Go to the path where sucess filea are stored

            latest_file_path = os.path.join(settings.MEDIA_ROOT, pd.uploaded_file.path)

            if os.path.exists(latest_file_path) and os.path.exists(uploaded_file.path):
                with open(latest_file_path, "rb") as previous_upload_file:
                    try:
                        checksum_previous = hashlib.sha256(
                            previous_upload_file.read()
                        ).hexdigest()

                    except IOError:
                        checksum_previous = None

                with open(uploaded_file.path, "rb") as new_upload_file:
                    try:
                        checksum_new = hashlib.sha256(
                            new_upload_file.read()
                        ).hexdigest()

                    except IOError:
                        checksum_new = None

                if (
                    checksum_previous is not None
                    and checksum_new is not None
                    and checksum_previous == checksum_new
                ):
                    raise EqualFileAlreadyUploaded("File is already in the database")

    except UploadHistory.DoesNotExist:
        pass

    #### Added For Checksum ##########################


def upload_data_to_tmp_table(data_source_id, file_metadata, pending_upload):
    # Upload New Data to a "temporary" table
    pending_upload.uploaded_file.seek(0)

    reader = pandas.read_csv(
        pending_upload.uploaded_file,
        header=0,
        dtype=file_metadata["types"],
        skip_blank_lines=False,
        index_col=False,
        names=file_metadata["columns"],
        chunksize=500,
    )

    all_mat_views = MaterializedQuery.objects.exclude(matviewname__contains="tmp")

    mat_views = {}

    for mat_view in all_mat_views:
        tmp_mat_view_name = mat_view.to_dict()["matviewname"] + "_tmp"

        # To run the mat views (with data) against the "temporary table"
        # To run for all mat views, as the data source can become with draft equal to true

        tmp_definition = mat_view.to_dict()["definition"].replace(
            "achilles_results", "achilles_results_tmp"
        )

        mat_views[tmp_mat_view_name] = [
            tmp_definition,
        ]

        # since draft can change with time, we must run the queries for all types of draft, namely with draft = true and draft = false
        if "draft = false" in tmp_definition:
            mat_views[tmp_mat_view_name].append(
                tmp_definition.replace("draft = false", "draft = true")
            )

    # Create "Temporary Upload" table, to store the data being uploaded
    # Refresh of Materialized views does not allow the refresh in Temporary Tables

    cache = caches["workers_locks"]  # To lock

    with RWLock(
        cache.client.get_client(), "celery_worker_updating", RWLock.WRITE, expire=None
    ):
        with transaction.atomic(), connections[
            "achilles"
        ].cursor() as cursor, settings.ACHILLES_DB_SQLALCHEMY_ENGINE.connect() as pandas_connection, pandas_connection.begin():
            try:
                cursor.execute("DROP TABLE IF EXISTS achilles_results_tmp CASCADE")
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS achilles_results_tmp AS SELECT * FROM "
                    + AchillesResults._meta.db_table
                    + " WHERE FALSE"
                )
                cursor.execute("CREATE SEQUENCE IF NOT EXISTS seq_id")
                cursor.execute(
                    "ALTER TABLE achilles_results_tmp ALTER COLUMN id SET DEFAULT nextval('seq_id')"
                )
                cursor.execute(
                    "ALTER TABLE achilles_results_tmp ALTER COLUMN id SET NOT NULL"
                )
                cursor.execute("SELECT setval('seq_id', 1)")

                # Upload data into "Temporary Table", similar structure to the actual upload process
                for chunk in reader:
                    chunk = chunk[chunk["stratum_1"].isin(["0"]) == False]  # noqa
                    chunk = chunk.assign(data_source_id=data_source_id)
                    chunk.to_sql(
                        "achilles_results_tmp",
                        pandas_connection,
                        if_exists="append",
                        index=False,
                    )
            except Exception:
                raise InvalidCSVFile("Error processing the file")

        # Fetch Materialized Views
        # The option here is to change the definitions of the original mat views and replace
        # the achilles_results references to achilles_results_tmp

        with transaction.atomic(), connections["achilles"].cursor() as cursor:
            try:
                for tmp_mat_view_name in mat_views:  # noqa
                    for tmp_definition in mat_views[tmp_mat_view_name]:
                        cursor.execute(
                            f"CREATE MATERIALIZED VIEW {tmp_mat_view_name} AS {tmp_definition}"
                        )
                        cursor.execute(f"DROP MATERIALIZED VIEW {tmp_mat_view_name}")
            except utils.DataError:
                cursor.execute("DROP TABLE IF EXISTS achilles_results_tmp CASCADE")
                raise FileDataCorrupted("Uploaded file is not valid")

        # Delete Temprary Upload data and its dependent (Materialzied Views)
        with transaction.atomic(), connections["achilles"].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS achilles_results_tmp CASCADE")
