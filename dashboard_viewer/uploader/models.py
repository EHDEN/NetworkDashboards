import datetime
import json
import os
import pathlib
import uuid

from django.conf import settings
from django.db import models
from django_celery_results.models import TaskResult


class Country(models.Model):
    class Meta:
        db_table = "country"
        ordering = ("country",)

    country = models.CharField(max_length=100, unique=True, help_text="Country name.")
    alpha2 = models.CharField(
        max_length=3, unique=True, help_text="ISO 3166-1 Alpha-2 Code"
    )
    continent = models.CharField(max_length=50, help_text="Continent associated.")

    def __str__(self):
        return f"{self.country}"

    def __repr__(self):
        return self.__str__()


class DatabaseType(models.Model):
    class Meta:
        db_table = "database_type"

    type = models.CharField(
        max_length=100, unique=True, help_text="Defines the database type."
    )

    def __str__(self):
        return self.type

    def __repr__(self):
        return self.__str__()


def hash_generator():
    return uuid.uuid4().hex


# Not following the relational rules in the database_type field, but it will simplify the SQL queries in the SQL Lab
class DataSource(models.Model):
    class Meta:
        db_table = "data_source"

    name = models.CharField(
        max_length=100, unique=True, help_text="Name of the data source."
    )
    acronym = models.CharField(
        max_length=50,
        unique=True,
        help_text="Short label for the data source, containing only letters, numbers, underscores or hyphens.",
    )
    hash = models.CharField(
        blank=True,
        default=hash_generator,
        max_length=255,
        null=False,
        unique=True,
    )
    release_date = models.CharField(
        max_length=50,
        help_text="Date at which DB is available for research for current release.",
        null=True,
        blank=True,
    )
    database_type = models.CharField(
        max_length=100, help_text="Type of the data source. You can create a new type."
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Country where the data source is located.",
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    link = models.URLField(help_text="Link to home page of the data source", blank=True)
    draft = models.BooleanField(default=True)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if DatabaseType.objects.filter(type=self.database_type).count() == 0:
            db_type = DatabaseType(type=self.database_type)
            db_type.save()

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


def failure_data_source_directory(instance, filename):
    file_path = os.path.join(
        settings.ACHILLES_RESULTS_STORAGE_PATH,
        instance.data_source.hash,
        "failure",
        "%Y%m%d%H%M%S%f" + "".join(pathlib.Path(filename).suffixes),
    )

    return datetime.datetime.now().strftime(file_path)


class PendingUpload(models.Model):
    STATE_PENDING = 1
    STATE_STARTED = 2
    STATE_CANCELED = 3
    STATE_FAILED = 4

    STATES = (
        (STATE_PENDING, "Pending"),
        (STATE_STARTED, "Started"),
        (STATE_CANCELED, "Canceled"),  # currently not being used
        (STATE_FAILED, "Failed"),
    )

    class Meta:
        ordering = ("-upload_date",)

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATES, default=STATE_PENDING)
    uploaded_file = models.FileField(upload_to=failure_data_source_directory)
    task_id = models.CharField(max_length=255, null=True)

    def get_status(self):
        for status_id, name in self.STATES:
            if self.status == status_id:
                return name

        return None  # should never happen

    def failure_message(self):
        if self.status != self.STATE_FAILED:
            return None

        try:
            task = TaskResult.objects.get(
                task_id=self.task_id, task_name="uploader.tasks.upload_results_file"
            )
        except TaskResult.DoesNotExist:
            return (
                "The information about this failure was deleted. Probably because this upload history "
                "record is an old one. If not please contact the system administrator for more details. "
            )

        result = json.loads(task.result)
        if result["exc_module"] == "uploader.file_handler.checks":
            return result["exc_message"][0]
        return (
            "An unexpected error occurred while processing your file. Please contact the "
            "system administrator for more details."
        )


def success_data_source_directory(instance, filename):
    file_path = os.path.join(
        settings.ACHILLES_RESULTS_STORAGE_PATH,
        instance.data_source.hash,
        "success",
        "%Y%m%d%H%M%S%f" + "".join(pathlib.Path(filename).suffixes),
    )

    return datetime.datetime.now().strftime(file_path)

def onboarding_folder(instance, filename):
    file_path = os.path.join(
        settings.ACHILLES_RESULTS_STORAGE_PATH,
        instance.data_source.hash,
        "onboarding",
        "%Y%m%d%H%M%S%f" + "".join(pathlib.Path(filename).suffixes),
    )
    return datetime.datetime.now().strftime(file_path)


class UploadHistory(models.Model):
    """
    Successful uploads only
    """

    class Meta:
        get_latest_by = "upload_date"
        ordering = ("-upload_date",)
        db_table = "upload_history"

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    r_package_version = models.CharField(max_length=50, null=True)
    generation_date = models.CharField(max_length=50, null=True)
    cdm_release_date = models.CharField(max_length=50, null=True)
    cdm_version = models.CharField(max_length=50, null=True)
    vocabulary_version = models.CharField(max_length=50, null=True)
    uploaded_file = models.FileField(
        null=True, upload_to=success_data_source_directory
    )  # For backwards compatibility its easier to make this null=True
    pending_upload_id = models.IntegerField(
        null=True,
        help_text="The id of the PendingUpload record that originated this successful upload."
        # aspedrosa: A foreign key is not used here since a PendingUpload record is erased once is successful. This
        #  is field is then only used to get the result data of pending upload through the get_upload_task_status view
    )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.data_source.name} - {self.upload_date}"

    def get_status(self):
        return "Done"


class AchillesResults(models.Model):
    class Meta:
        db_table = "achilles_results"
        indexes = [
            models.Index(fields=("data_source",)),
            models.Index(fields=("analysis_id",)),
        ]

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    analysis_id = models.BigIntegerField()
    stratum_1 = models.TextField(null=True)
    stratum_2 = models.TextField(null=True)
    stratum_3 = models.TextField(null=True)
    stratum_4 = models.TextField(null=True)
    stratum_5 = models.TextField(null=True)
    count_value = models.BigIntegerField()
    min_value = models.FloatField(null=True)
    max_value = models.FloatField(null=True)
    avg_value = models.FloatField(null=True)
    stdev_value = models.FloatField(null=True)
    median_value = models.FloatField(null=True)
    p10_value = models.FloatField(null=True)
    p25_value = models.FloatField(null=True)
    p75_value = models.FloatField(null=True)
    p90_value = models.FloatField(null=True)


class AchillesResultsArchive(models.Model):
    class Meta:
        db_table = "achilles_results_archive"
        indexes = [
            models.Index(fields=("data_source",)),
            models.Index(fields=("analysis_id",)),
        ]

    upload_info = models.ForeignKey(UploadHistory, on_delete=models.CASCADE)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    analysis_id = models.BigIntegerField()
    stratum_1 = models.TextField(null=True)
    stratum_2 = models.TextField(null=True)
    stratum_3 = models.TextField(null=True)
    stratum_4 = models.TextField(null=True)
    stratum_5 = models.TextField(null=True)
    count_value = models.BigIntegerField()
    min_value = models.FloatField(null=True)
    max_value = models.FloatField(null=True)
    avg_value = models.FloatField(null=True)
    stdev_value = models.FloatField(null=True)
    median_value = models.FloatField(null=True)
    p10_value = models.FloatField(null=True)
    p25_value = models.FloatField(null=True)
    p75_value = models.FloatField(null=True)
    p90_value = models.FloatField(null=True)

class OnboardingReport(models.Model):
    class Meta:
        db_table = "onboarding_report"
    
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    uploaded_file = models.FileField(
        null=True, upload_to=onboarding_folder
    )

    def get_status(self):
        return "Done"