import csv
import datetime
import io
import re
import zipfile

import numpy  # noqa
import pandas
from django.contrib import messages
from django.utils.html import mark_safe

VERSION_REGEX = re.compile(r"\d+(\.\d+)*")


def handle_zip(request):
    """
    1. Validates the zip received
    2. Extract the data on the csvs to pandas Dataframes
    4. From achilles_results.csv several mandatory fields are also retrieved
     to create an UploadHistory record
    3. Merges the dataframes from both achilles_results and achilles_result_dist
    The zip

    :param request: view request
    :return: If there is something wrong with the zipfile and its files
     this function returns None
    """

    try:
        uploaded_zipfile = zipfile.ZipFile(request.FILES["achilles_results_files"])
    except zipfile.BadZipFile:
        messages.error(
            request,
            mark_safe("Invalid zip file provided."),
        )

        return None

    if "achilles_results.csv" not in uploaded_zipfile.namelist():
        messages.error(
            request,
            mark_safe(
                '"achilles_results.csv" file not present on the upload zip file.'
            ),
        )

        return None

    with uploaded_zipfile.open("achilles_results.csv") as achilles_results_file:
        expected_columns = [
            "analysis_id",
            "stratum_1",
            "stratum_2",
            "stratum_3",
            "stratum_4",
            "stratum_5",
            "count_value",
        ]
        data = _read_dataframe_from_csv(
            request, "achilles_results.csv", achilles_results_file, expected_columns
        )

    if data is None:
        return None
    data = _extract_mandatory_fields_from_achilles_results(request, data)
    if data is None:
        return None

    dist_data = None
    if "achilles_results_dist.csv" in uploaded_zipfile.namelist():
        with uploaded_zipfile.open(
            "achilles_results_dist.csv"
        ) as achilles_results_dist_file:
            expected_columns.extend(
                [
                    "min_value",
                    "max_value",
                    "avg_value",
                    "stdev_value",
                    "median_value",
                    "p10_value",
                    "p25_value",
                    "p75_value",
                    "p90_value",
                ]
            )
            dist_data = _read_dataframe_from_csv(
                request,
                "achilles_results_dist.csv",
                achilles_results_dist_file,
                expected_columns,
            )

        if dist_data is None:
            return None

    if dist_data is not None:
        data["achilles_results"] = pandas.concat(
            [data["achilles_results"], dist_data], ignore_index=True, copy=False
        )

    request.FILES["achilles_results_files"].seek(0)

    return data


def _read_dataframe_from_csv(request, filename, file, expected_columns):
    """
    Validates and Converts the csv content of a received file to a Dataframe.
    :param request: view request
    :param filename: name of the file being processed
    :param file: file object of the file being processed
    :param expected_columns: names of the expected columns to get on the dataframe
    :return: If the csv doesn't not have the expected structure (specific number of columns
     and correct field types) this function returns none.
    """

    wrapper = io.TextIOWrapper(file)
    csv_reader = csv.reader(wrapper)

    # read just the first line to check the number of column according to the header
    first_row = next(csv_reader)
    wrapper.detach()

    if len(first_row) != len(expected_columns):
        messages.error(
            request,
            mark_safe(
                f'The file "{filename}" has an invalid number of columns. '
                f"Expected {len(expected_columns)} found {len(first_row)}."
            ),
        )

        return None

    file.seek(0)

    try:
        achilles_results = pandas.read_csv(
            file,
            header=0,
            dtype=str,
            skip_blank_lines=False,
            index_col=False,
            names=expected_columns,
        )
    except ValueError:
        messages.error(
            request,
            mark_safe(
                f'The file "{filename}" has an invalid csv format. Make sure is a text file separated'
                f" by <b>commas</b> and you have {len(expected_columns)} columns."
            ),
        )

        return None

    if achilles_results[["analysis_id", "count_value"]].isna().values.any():
        messages.error(
            request,
            mark_safe(
                f'Some rows of the file "{filename}" have null values either '
                'on the column "analysis_id" or "count_value".'
            ),
        )

        return None

    # validate field types
    try:
        achilles_results = achilles_results.astype(
            {
                "analysis_id": numpy.int64,
                "count_value": numpy.int64,
            },
        )
        if len(achilles_results.columns) == 16:
            achilles_results = achilles_results.astype(
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
            achilles_results = achilles_results.astype(
                {
                    "min_value": "Int64",
                    "max_value": "Int64",
                    "median_value": "Int64",
                    "p10_value": "Int64",
                    "p25_value": "Int64",
                    "p75_value": "Int64",
                    "p90_value": "Int64",
                },
            )
            # Why are you converting two times ?
            # https://stackoverflow.com/questions/60024262/error-converting-object-string-to-int32-typeerror-object-cannot-be-converted
    except ValueError:
        messages.error(
            request,
            mark_safe(
                f'The file "{filename}" has invalid values on some columns. Remember that only '
                'the "stratum_*" columns accept strings, all the other fields expect numeric types.'
            ),
        )

        return None

    return achilles_results


def _extract_mandatory_fields_from_achilles_results(request, achilles_results):
    """
    On the achilles_results.csv file there are several fields on the analysis id
     0 and 5000 that are used to build a UploadHistory record.
    On this function they are extracted and validated.
    :param request: view request
    :param achilles_results: dataframe extract from the csv
    :return: If there is some field with errors then this function returns None.
     If not, a dictionary is returned with the several mandatory fields
     for the UploadHistory model and the achilles_results dataframe.
    """
    output = _check_correct(
        ["0", "5000"],
        [0, 5000],
        lambda e: achilles_results[achilles_results.analysis_id == e],
        lambda e: not e.empty,
    )

    if isinstance(output, str):
        messages.error(
            request,
            mark_safe(
                f'Analysis id{output} missing on the "achilles_results.csv" file. Try (re)running the plugin '
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            ),
        )

        return None

    return_value = {"achilles_results": achilles_results}

    analysis_0 = output[0].reset_index()
    analysis_5000 = output[1].reset_index()

    errors = []

    # check mandatory dates
    output = _check_correct(
        [
            "Generation date (analysis_id=0, stratum3)",
            "Source release date (analysis_id=5000, stratum_2)",
            "CDM release date (analysis_id=5000, stratum_3)",
        ],
        [
            (analysis_0, "stratum_3"),
            (analysis_5000, "stratum_2"),
            (analysis_5000, "stratum_3"),
        ],
        _convert_to_datetime_from_iso,
        lambda date: date,
    )

    if isinstance(output, str):
        errors.append(f"The field{output} not in a ISO date format.")
    else:
        return_value["generation_date"] = output[0]
        return_value["source_release_date"] = output[1]
        return_value["cdm_release_date"] = output[2]

    # check mandatory versions
    output = _check_correct(
        [
            "CDM version (analysis_id=0, stratum_1)",
            "R Package version (analysis_id=5000, stratum_4)",
            "Vocabulary version (analysis_id=5000, stratum_5)",
        ],
        [
            (analysis_0, "stratum_2"),
            (analysis_5000, "stratum_4"),
            (analysis_5000, "stratum_5"),
        ],
        lambda elem: elem[0].loc[0, elem[1]],
        lambda version: VERSION_REGEX.fullmatch(version)
        if version and isinstance(version, str)
        else None,
    )

    if isinstance(output, str):
        errors.append(f"The field{output} not in a valid version format.")
    else:
        return_value["cdm_version"] = output[0]
        return_value["r_package_version"] = output[1]
        return_value["vocabulary_version"] = output[2]

    if errors:
        error_message = [
            'Some fields on the file "achilles_results.csv" have invalid format:<br/><ul>'
        ]
        for error in errors:
            error_message.append(f"<li>{error}</li>")
        error_message.append(
            "</ul><br/>Try (re)running the plugin "
            "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
            " on your database."
        )
        messages.error(
            request,
            mark_safe("".join(error_message)),
        )
        return None

    return return_value


def _convert_to_datetime_from_iso(elem):
    """
    Function used to convert string dates received on the uploaded file.
    Used on the 'transform' argument of the function 'check_correct'.

    :param elem: string to convert to datetime
    :return: a datetime object or None if the string is not in a valid ISO format
    """
    analysis, stratum = elem

    result = analysis.loc[0, stratum]
    if not result or not isinstance(result, str):
        return None

    try:
        return datetime.datetime.fromisoformat(result)
    except ValueError:  # Invalid date format
        return None


def _check_correct(names, values, transform, check):
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

    for i, _ in enumerate(names):
        transformed = transform(values[i])
        if not check(transformed):
            bad_elements.append(names[i])
        else:
            transformed_elements[i] = transformed

    if bad_elements:
        return (
            f" {bad_elements[0]} is"
            if len(bad_elements) == 1
            else f"s {', '.join(bad_elements[:-1])} and {bad_elements[-1]} are"
        )

    return transformed_elements
