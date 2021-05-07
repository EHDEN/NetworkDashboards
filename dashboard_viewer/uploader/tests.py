import datetime

from django.test import SimpleTestCase, TestCase

from .models import (
    AchillesResults,
    AchillesResultsArchive,
    AchillesResultsDraft,
    Country,
    DataSource,
    UploadHistory,
)
from .tasks import update_achilles_results_data


class DataSourceCreator:
    def __init__(self):
        self._counter = 0

    def create(self, draft):
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
            draft=draft,
        )


datasource_creator = DataSourceCreator()


class DraftChangeTestCase(TestCase):
    databases = "__all__"

    records_count = 5

    @staticmethod
    def _create_data(draft, insert_achilles=True):
        db = datasource_creator.create(draft)

        if insert_achilles:
            records_class = AchillesResultsDraft if draft else AchillesResults
            records_class.objects.bulk_create(
                records_class(data_source=db, analysis_id=i, count_value=i)
                for i in range(DraftChangeTestCase.records_count)
            )

        return db

    def test_dedraft(self):
        db = self._create_data(True)
        db.draft = False
        db.save()

        self.assertEqual(
            DraftChangeTestCase.records_count, AchillesResults.objects.count()
        )
        self.assertEqual(0, AchillesResultsDraft.objects.count())
        self.assertEqual(0, AchillesResultsArchive.objects.count())

    def test_makedraft(self):
        db = self._create_data(False)
        db.draft = True
        db.save()

        self.assertEqual(0, AchillesResults.objects.count())
        self.assertEqual(
            DraftChangeTestCase.records_count, AchillesResultsDraft.objects.count()
        )
        self.assertEqual(0, AchillesResultsArchive.objects.count())

    def test_empty_makedraft(self):
        db = self._create_data(False, False)
        db.draft = True
        try:
            db.save()
        except:
            self.fail()

        self.assertEqual(0, AchillesResults.objects.count())
        self.assertEqual(0, AchillesResultsDraft.objects.count())
        self.assertEqual(0, AchillesResultsArchive.objects.count())

    def test_empty_dedraft(self):
        db = self._create_data(True, False)
        db.draft = False
        try:
            db.save()
        except:
            self.fail()

        self.assertEqual(0, AchillesResults.objects.count())
        self.assertEqual(0, AchillesResultsDraft.objects.count())
        self.assertEqual(0, AchillesResultsArchive.objects.count())


class InsertAchillesResultsTestCase(SimpleTestCase):
    databases = "__all__"
    records = (
        '[{"analysis_id": 1, "count_value": 1}, {"analysis_id": 2, "count_value": 2}]'
    )

    @classmethod
    def setUpClass(cls):
        super(InsertAchillesResultsTestCase, cls).setUpClass()
        cls.db = datasource_creator.create(True)

    def setUp(self) -> None:
        AchillesResults.objects.filter().delete()
        AchillesResultsArchive.objects.filter().delete()
        AchillesResultsDraft.objects.filter().delete()

    def _update_and_check(self, last_upload_id, count, draft_count, archive_count):
        task = update_achilles_results_data.delay(
            self.db.id, last_upload_id, self.records
        )
        task.wait(timeout=None)

        self.assertEqual(count, AchillesResults.objects.count())
        self.assertEqual(draft_count, AchillesResultsDraft.objects.count())
        self.assertEqual(archive_count, AchillesResultsArchive.objects.count())

    def test_insert_draft(self):
        if not self.db.draft:
            self.db.draft = True
            self.db.save()

        self._update_and_check(None, 0, 2, 0)
        last_upload_id = UploadHistory.objects.create(
            data_source=self.db, upload_date=datetime.datetime.now()
        ).id
        self._update_and_check(last_upload_id, 0, 2, 2)
        last_upload_id = UploadHistory.objects.create(
            data_source=self.db, upload_date=datetime.datetime.now()
        ).id
        self._update_and_check(last_upload_id, 0, 2, 4)

    def test_insert_nondraft(self):
        if self.db.draft:
            self.db.draft = False
            self.db.save()

        self._update_and_check(None, 2, 0, 0)
        last_upload_id = UploadHistory.objects.create(
            data_source=self.db, upload_date=datetime.datetime.now()
        ).id
        self._update_and_check(last_upload_id, 2, 0, 2)
        last_upload_id = UploadHistory.objects.create(
            data_source=self.db, upload_date=datetime.datetime.now()
        ).id
        self._update_and_check(last_upload_id, 2, 0, 4)

    def test_move_records_of_only_one_db(self):
        db2 = datasource_creator.create(self.db.draft)

        task = update_achilles_results_data.delay(self.db.id, None, self.records)
        task.wait(timeout=None)

        task = update_achilles_results_data.delay(db2.id, None, self.records)
        task.wait(timeout=None)
        # counts are at -> (4, 0, 0) or (0, 4, 0)

        last_upload_id = UploadHistory.objects.create(
            data_source=self.db, upload_date=datetime.datetime.now()
        ).id

        if self.db.draft:
            counts = (0, 4)
        else:
            counts = (4, 0)
        self._update_and_check(last_upload_id, *counts, 2)
