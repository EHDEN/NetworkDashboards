import csv
import io
import zipfile

import numpy  # noqa
import pandas
from django.contrib import messages
from django.utils.html import mark_safe


def handle(request):
    upload_filename = request.FILES["achilles_results_files"].name
    if upload_filename.endswith(".zip"):
        return _handle_zip(request)
    if upload_filename.endswith(".csv"):
        normal_expected_columns = [
            "analysis_id",
            "stratum_1",
            "stratum_2",
            "stratum_3",
            "stratum_4",
            "stratum_5",
            "count_value",
        ]
        achilles_results = _read_dataframe_from_csv(
            request,
            request.FILES["achilles_results_files"],
            [
                normal_expected_columns,
                [
                    *normal_expected_columns,
                    "min_value",
                    "max_value",
                    "avg_value",
                    "stdev_value",
                    "median_value",
                    "p10_value",
                    "p25_value",
                    "p75_value",
                    "p90_value",
                ],
            ],
        )

        if achilles_results is None:
            return None

        data = _extract_mandatory_fields_from_achilles_results(request, achilles_results)

        if data is None:
            return None

        data["achilles_results"] = achilles_results

        return data

    messages.error(
        request,
        "Unknown file format. Upload either a zip or a csv file.",
    )

    return None


def _handle_zip(request):
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
            "Invalid zip file provided.",
        )

        return None

    if "achilles_results.csv" not in uploaded_zipfile.namelist():
        messages.error(
            request,
            '"achilles_results.csv" file not present on the upload zip file.',
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
        achilles_results = _read_dataframe_from_csv(
            request, achilles_results_file, [expected_columns], "achilles_results.csv"
        )

    if achilles_results is None:
        return None
    data = _extract_mandatory_fields_from_achilles_results(request, achilles_results)
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
                achilles_results_dist_file,
                [expected_columns],
                "achilles_results_dist.csv",
            )

        if dist_data is None:
            return None

    if dist_data is not None:
        achilles_results = pandas.concat(
            [achilles_results, dist_data], ignore_index=True, copy=False
        )

    request.FILES["achilles_results_files"].seek(0)

    data["achilles_results"] = achilles_results

    return data


def _read_dataframe_from_csv(request, file, allowed_headers, filename=None):
    """
    Validates and Converts the csv content of a received file to a Dataframe.
    :param request: view request
    :param file: file object of the file being processed
    :param allowed_headers: list of all possible headers
    :param filename: name of the file being processed
    :return: If the csv doesn't not have the expected structure (specific number of columns
     and correct field types) this function returns none.
    """
    assert len(allowed_headers) >= 1

    csv_reader = csv.reader(io.StringIO(file.readline().decode("utf-8")))

    # read just the first line to check the number of column according to the header
    first_row = next(csv_reader)

    expected_columns = None
    for header in allowed_headers:
        if len(header) == len(first_row):
            expected_columns = header
            break

    if expected_columns is None:
        expected_amounts = (
            allowed_headers[0]
            if len(allowed_headers) == 1
            else ", ".join([str(len(header)) for header in allowed_headers[:-1]])
            + f" or {len(allowed_headers[:-1])}"
        )
        filename_to_present = f'file "{filename}"' if filename is not None else "uploaded file"
        messages.error(
            request,
            f"The {filename_to_present} has an invalid number of columns. "
            f"Expected {expected_amounts} found {len(first_row)}.",
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
            f'Some rows of the file "{filename}" have null values either '
            'on the column "analysis_id" or "count_value".',
        )

        return None

    # validate field types
    try:
        dict_type = {
            "analysis_id": numpy.int64,
            "count_value": numpy.int64,
        }
        if len(achilles_results.columns) == 16:
            dict_type.update(
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
        achilles_results = achilles_results.astype(dict_type, copy=False)
    except ValueError:
        messages.error(
            request,
            f'The file "{filename}" has invalid values on some columns. Remember that only '
            'the "stratum_*" columns accept strings, all the other fields expect numeric types.',
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
        lambda e: not e.empty,
        lambda e: achilles_results[achilles_results.analysis_id == e],
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

    analysis_0 = output[0].reset_index()
    analysis_5000 = output[1].reset_index()

    output = _check_correct(
        ["0", "5000"],
        [analysis_0, analysis_5000],
        lambda e: len(e) == 1,
    )
    if isinstance(output, str):
        messages.error(
            request,
            mark_safe(
                f"Analysis id{output} duplicated on multiple rows. Try (re)running the plugin "
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            ),
        )
        return None

    # check mandatory dates
    output = _check_correct(
        [
            "Generation date (analysis_id=0, stratum3)",
            "Source release date (analysis_id=5000, stratum_2)",
            "CDM release date (analysis_id=5000, stratum_3)",
            "CDM version (analysis_id=0, stratum_1)",
            "R Package version (analysis_id=5000, stratum_4)",
            "Vocabulary version (analysis_id=5000, stratum_5)",
        ],
        [
            (analysis_0, "stratum_3"),
            (analysis_5000, "stratum_2"),
            (analysis_5000, "stratum_3"),
            (analysis_0, "stratum_2"),
            (analysis_5000, "stratum_4"),
            (analysis_5000, "stratum_5"),
        ],
        lambda value: not pandas.isna(value) and value,
        lambda value: value[0].loc[0, value[1]],
    )

    if isinstance(output, str):
        messages.error(
            request,
            mark_safe(
                f"The field{output} mandatory. Try (re)running the plugin "
                "<a href='https://github.com/EHDEN/CatalogueExport'>CatalogueExport</a>"
                " on your database."
            ),
        )
        return None

    return {
        key: output[i]
        for i, key in enumerate([
            "generation_date",
            "source_release_date",
            "cdm_release_date",
            "cdm_version",
            "r_package_version",
            "vocabulary_version",
        ])
    }


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
        transformed = values[i] if transform is None else transform(values[i])
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
