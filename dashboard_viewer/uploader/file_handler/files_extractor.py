import zipfile
from enum import Enum

from uploader.file_handler.errors import BothNomenclaturesUsed, InvalidZipFile, NoExpectedFiles, UnsupportedExtension


class ResultsFileType(Enum):
    UNKNOWN = 0
    NORMAL = 0
    DIST = 0


def extract_files(uploaded_file):
    if uploaded_file.name.endswith(".zip"):
        return _extract_from_zip(uploaded_file)
    if uploaded_file.name.endswith(".csv"):
        return (uploaded_file, ResultsFileType.UNKNOWN),

    raise UnsupportedExtension()


def _extract_from_zip(uploaded_file):
    try:
        uploaded_zipfile = zipfile.ZipFile(uploaded_file)
    except zipfile.BadZipFile:
        raise InvalidZipFile()

    results_filename = results_dist_filename = None
    prefixes = ("achilles", "catalogue")
    prefix_idx = 0
    for i, prefix in enumerate(prefixes):
        results_filename_tmp = prefix + "_results.csv"
        if results_filename_tmp in uploaded_zipfile.namelist():
            if results_filename is not None:  # contains both nomenclatures
                raise BothNomenclaturesUsed()

            results_filename = results_filename_tmp
            results_dist_filename = prefix + "_results_dist.csv"
            prefix_idx = i

    if results_filename is None:  # contains no expected files
        raise NoExpectedFiles()

    if (
        prefixes[(prefix_idx + 1) % 2] + "_results_dist.csv"
        in uploaded_zipfile.namelist()
    ):
        messages.warning(
            request,
            "The uploaded zip contains a dist file with a different prefix "
            f"({prefixes[(prefix_idx + 1) % 2]}_results_dist.csv) from the main results file ({results_filename}). "
            "As a result, the dist file will be ignored.",
        )

    main_results_file = (uploaded_zipfile.open(results_filename), ResultsFileType.NORMAL)
    if results_dist_filename in uploaded_zipfile.namelist():
        return main_results_file, (uploaded_zipfile.open(results_dist_filename), ResultsFileType.DIST)
    return main_results_file,
