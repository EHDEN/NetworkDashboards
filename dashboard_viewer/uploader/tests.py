import io
import logging

import numpy
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, tag, TestCase, TransactionTestCase

from .file_handler.checks import (
    DuplicatedMetadataRow,
    EqualFileAlreadyUploaded,
    extract_data_from_uploaded_file,
    FileChecksException,
    InvalidFieldValue,
    InvalidFileFormat,
    MissingFieldValue,
)
from .file_handler.updates import update_achilles_results_data
from .models import (
    AchillesResults,
    AchillesResultsArchive,
    Country,
    DataSource,
    PendingUpload,
    UploadHistory,
)
from .tasks import upload_results_file


@tag("third-party-app")
@override_settings(ALLOWED_HOSTS=["thisapp.host.com", "mainapp.host.com"])
class UploaderRestrictedAccess(TestCase):
    """
    Assumes the following environment variables values:
      SINGLE_APPLICATION_MODE=n
      MAIN_APPLICATION_HOST=mainapp.host.com
    """

    databases = "__all__"

    def test_block_if_wrong_host(self):
        response = self.client.get("/uploader/test/", HTTP_HOST="thisapp.host.com")

        self.assertEqual(403, response.status_code)

    def test_not_block_if_correct_host(self):
        response = self.client.get("/uploader/test/", HTTP_HOST="mainapp.host.com")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header("X-Frame-Options"))
        self.assertEqual(
            "ALLOW-FROM HTTPS://MAINAPP.HOST.COM/", response["X-Frame-Options"]
        )

    def test_not_block_other_urls(self):
        response = self.client.get("/admin/login/", HTTP_HOST="thisapp.host.com")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.has_header("X-Frame-Options"))
        self.assertEqual(
            "ALLOW-FROM HTTPS://MAINAPP.HOST.COM/", response["X-Frame-Options"]
        )


class UploaderNonRestrictedAccess(TestCase):
    """
    Assumes the following environment variables values:
      SINGLE_APPLICATION_MODE=y
    """

    databases = "__all__"

    @override_settings(ALLOWED_HOSTS=["some.domain.com"])
    def test_not_block_if_single_application(self):
        response = self.client.get("/uploader/test/", HTTP_HOST="some.domain.com")

        self.assertEqual(200, response.status_code)
        if response.has_header("X-Frame-Options"):
            self.assertNotIn("ALLOW-FROM ", response.get("X-Frame-Options"))


class DataSourceCreator:
    def __init__(self):
        self._counter = 0

    def create(self):
        self._counter += 1
        return DataSource.objects.create(
            name=f"test{self._counter}",
            acronym=f"test{self._counter}",
            release_date="10/13/2020",
            database_type="Test",
            country=Country.objects.get_or_create(country="test", continent="test")[0],
            latitude=0,
            longitude=0,
            link="",
        )


datasource_creator = DataSourceCreator()


class UpdateAchillesResultsDataTestCase(TransactionTestCase):
    databases = "__all__"

    file_metadata = {
        "columns": [
            "analysis_id",
            "stratum_1",
            "stratum_2",
            "stratum_3",
            "stratum_4",
            "stratum_5",
            "count_value",
        ],
        "types": {
            "analysis_id": numpy.int64,
            "stratum_1": "string",
            "stratum_2": "string",
            "stratum_3": "string",
            "stratum_4": "string",
            "stratum_5": "string",
            "count_value": numpy.int64,
        },
    }
    file = io.StringIO(
        ",".join(file_metadata["columns"]) + "\n" "0,,,,,,1000\n" "5000,,,,,,1001\n"
    )

    fixtures = ("countries", "two_data_sources")

    def __init__(self, *args, **kwargs):
        super(UpdateAchillesResultsDataTestCase, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(UpdateAchillesResultsDataTestCase.__name__)
        self._pending_upload = PendingUpload(
            id=1,
            uploaded_file=self.file,
        )

    def setUp(self) -> None:
        self._pending_upload.data_source = DataSource.objects.get(acronym="test1")

    def _update_and_check(self, count, archive_count):
        self._pending_upload.uploaded_file.seek(0)
        update_achilles_results_data(
            self._logger,
            self._pending_upload,
            self.file_metadata,
        )
        UploadHistory.objects.create(
            data_source=DataSource.objects.get(acronym="test1")
        )

        self.assertEqual(count, AchillesResults.objects.count())
        self.assertEqual(archive_count, AchillesResultsArchive.objects.count())

    def test_insert(self):
        self._update_and_check(2, 0)
        self._update_and_check(2, 2)
        self._update_and_check(2, 4)

    def test_move_records_of_only_one_db(self):
        self._pending_upload.uploaded_file.seek(0)
        update_achilles_results_data(
            self._logger, self._pending_upload, self.file_metadata
        )
        UploadHistory.objects.create(
            data_source=DataSource.objects.get(acronym="test1")
        )

        self._pending_upload.uploaded_file.seek(0)
        self._pending_upload.data_source = DataSource.objects.get(acronym="test2")
        update_achilles_results_data(
            self._logger, self._pending_upload, self.file_metadata
        )
        UploadHistory.objects.create(
            data_source=DataSource.objects.get(acronym="test2")
        )

        self.assertEqual(4, AchillesResults.objects.count())
        self.assertEqual(0, AchillesResultsArchive.objects.count())

        self._pending_upload.data_source = DataSource.objects.get(acronym="test1")
        self._update_and_check(4, 2)


class ExtractDataFromUploadedFileTestCase(TestCase):
    file_7 = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
            "0,,3,0,,,1000\n"
            "5000,,1,,2,4,1001\n",
            "utf8",
        )
    )
    file_16 = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count,min,max,avg,std,mean,p10,p25,p75,p90\n"
            "0,,,,,,1000,,,,,,,,,\n"
            "5000,,,,,,1001,4,4.5,2,5,5.3,3,3,4,3.44\n",
            "utf8",
        )
    )

    file_7_invalid_column_count = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
            "0,,,,,,1000\n"
            "1,,,,,,1000,,,,,\n",
            "utf8",
        )
    )

    file_7_invalid_types = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
            "0,,,,,,notanumber\n",
            "utf8",
        )
    )

    file_7_mandatory_empty = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
            ",,,,,,1\n",
            "utf8",
        )
    )

    file_7_missing_0 = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
            "1,,,,,,1\n",
            "utf8",
        )
    )

    file_7_duplicated = io.BytesIO(
        bytes(
            "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
            "0,,,,,,1\n"
            "0,,,,,,1\n",
            "utf8",
        )
    )

    def test_all_good_7(self):
        self.file_7.seek(0)

        try:
            extract_data_from_uploaded_file(self.file_7)
        except FileChecksException:
            self.fail("Exception raised")

    def test_all_good_16(self):
        try:
            extract_data_from_uploaded_file(self.file_16)
        except FileChecksException:
            self.fail("Exception raised")

    def test_invalid_column_count(self):
        self.assertRaises(
            InvalidFileFormat,
            extract_data_from_uploaded_file,
            self.file_7_invalid_column_count,
        )

    def test_invalid_types(self):
        self.assertRaises(
            InvalidFieldValue,
            extract_data_from_uploaded_file,
            self.file_7_invalid_types,
        )

    def test_mandatory_empty(self):
        self.assertRaises(
            InvalidFieldValue,
            extract_data_from_uploaded_file,
            self.file_7_mandatory_empty,
        )

    def test_missing_analysis_id_0(self):
        self.assertRaises(
            MissingFieldValue, extract_data_from_uploaded_file, self.file_7_missing_0
        )

    def test_duplicated_analysis_id_0(self):
        self.assertRaises(
            DuplicatedMetadataRow,
            extract_data_from_uploaded_file,
            self.file_7_duplicated,
        )

    def test_return_value(self):
        self.file_7.seek(0)

        file_metadata, metadata = extract_data_from_uploaded_file(self.file_7)

        self.assertEquals(
            metadata,
            {
                "generation_date": "0",
                "source_release_date": "1",
                "cdm_release_date": None,
                "cdm_version": "2",
                "r_package_version": "3",
                "vocabulary_version": "4",
            },
        )

        self.assertEquals(
            file_metadata, UpdateAchillesResultsDataTestCase.file_metadata
        )


class UploadResultsFileTestCase(TransactionTestCase):
    databases = "__all__"

    fixtures = ("countries", "two_data_sources")

    # files that fail lead to django closing them somewhere so I store the content here
    #  instead of using the BytesIO pointer of the ExtractDataFromUploadedFileTestCase class
    file_7_invalid_column_count = bytes(
        "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
        "0,,,,,,1000\n"
        "1,,,,,,1000,,,,,\n",
        "utf8",
    )

    def test_invalid_file(self):
        pending_upload_id = PendingUpload.objects.create(
            data_source=DataSource.objects.get(acronym="test1"),
            uploaded_file=SimpleUploadedFile(
                "dummy",
                self.file_7_invalid_column_count,
            ),
        ).id

        try:
            upload_results_file.delay(pending_upload_id)
        except InvalidFileFormat:
            pass

        self.assertEqual(
            PendingUpload.objects.get(id=pending_upload_id).status,
            PendingUpload.STATE_FAILED,
        )

    def test_valid_file(self):
        ExtractDataFromUploadedFileTestCase.file_7.seek(0)

        pending_upload = PendingUpload.objects.create(
            data_source=DataSource.objects.get(acronym="test1"),
            uploaded_file=SimpleUploadedFile(
                "dummy", ExtractDataFromUploadedFileTestCase.file_7.read()
            ),
        )

        pending_upload_id = pending_upload.id
        upload_results_file.delay(pending_upload_id)

        self.assertRaises(
            PendingUpload.DoesNotExist, PendingUpload.objects.get, id=pending_upload_id
        )
        self.assertEqual(0, cache.get("celery_workers_updating"))

        try:
            UploadHistory.objects.get(pending_upload_id=pending_upload_id)
        except UploadHistory.DoesNotExist:
            self.fail(
                "No upload history record with the associated pending upload id created"
            )

    def test_invalid_file_due_to_checksum(self):
        ExtractDataFromUploadedFileTestCase.file_7.seek(0)

        pending_upload_1 = PendingUpload.objects.create(
            data_source=DataSource.objects.get(acronym="test1"),
            uploaded_file=SimpleUploadedFile(
                "dummy", ExtractDataFromUploadedFileTestCase.file_7.read()
            ),
        )

        upload_results_file.delay(pending_upload_1.id)

        # Upload the second file, with equal data

        ExtractDataFromUploadedFileTestCase.file_7.seek(0)

        new_pending_upload = PendingUpload.objects.create(
            data_source=DataSource.objects.get(acronym="test1"),
            uploaded_file=SimpleUploadedFile(
                "dummy", ExtractDataFromUploadedFileTestCase.file_7.read()
            ),
        )

        try:
            upload_results_file.delay(new_pending_upload.id)
        except EqualFileAlreadyUploaded:
            pass

        self.assertEqual(
            PendingUpload.objects.get(id=new_pending_upload.id).status,
            PendingUpload.STATE_FAILED,
        )

    def test_valid_file_checksum(self):
        ExtractDataFromUploadedFileTestCase.file_7.seek(0)

        pending_upload_1 = PendingUpload.objects.create(
            data_source=DataSource.objects.get(acronym="test1"),
            uploaded_file=SimpleUploadedFile(
                "dummy", ExtractDataFromUploadedFileTestCase.file_7.read()
            ),
        )

        upload_results_file.delay(pending_upload_1.id)

        # Upload the second file, with different data

        new_file = io.BytesIO(
            bytes(
                "analysis_id,stratum_1,stratum_2,stratum_3,stratum_4,stratum_5,count_value\n"
                "0,,5,0,,,2000\n"
                "5000,,1,,2,4,1001\n",
                "utf8",
            )
        )

        new_pending_upload = PendingUpload.objects.create(
            data_source=DataSource.objects.get(acronym="test1"),
            uploaded_file=SimpleUploadedFile("dummy", new_file.read()),
        )

        try:
            upload_results_file.delay(new_pending_upload.id)
        except EqualFileAlreadyUploaded:
            self.fail("File is already in database")

        self.assertRaises(
            PendingUpload.DoesNotExist,
            PendingUpload.objects.get,
            id=new_pending_upload.id,
        )

        self.assertEqual(0, cache.get("celery_workers_updating"))

        try:
            UploadHistory.objects.get(pending_upload_id=new_pending_upload.id)
        except UploadHistory.DoesNotExist:
            self.fail(
                "No upload history record with the associated pending upload id created"
            )
