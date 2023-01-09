import csv
import hashlib
import io
import os

import numpy
import pandas
from django.conf import settings

from uploader.models import DataSource, UploadHistory


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

    try:
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
