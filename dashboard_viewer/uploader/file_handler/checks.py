import csv
import io

import numpy
import pandas


class FileChecksException(Exception):
    pass


class InvalidFileFormat(FileChecksException):
    pass


class InvalidFieldValue(FileChecksException):
    pass


class DuplicateMetadataRow(FileChecksException):
    pass


class MissingFieldValue(FileChecksException):
    pass


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

    first_row = next(csv_reader)
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
        raise InvalidFileFormat("The provided file has an invalid number of columns.")

    uploaded_file.seek(0)

    file_reader = pandas.read_csv(
        uploaded_file,
        header=0,
        dtype=str,
        skip_blank_lines=False,
        index_col=False,
        names=columns,
        chunksize=100,
    )

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
            raise DuplicateMetadataRow(
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
