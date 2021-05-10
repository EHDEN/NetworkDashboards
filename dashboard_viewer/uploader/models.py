from django.db import models


class Country(models.Model):
    class Meta:
        db_table = "country"
        ordering = ("country",)

    country = models.CharField(max_length=100, unique=True, help_text="Country name.")
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
    release_date = models.CharField(
        max_length=50,
        help_text="Date at which DB is available for research for current release.",
        null=True,
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


class UploadHistory(models.Model):
    class Meta:
        ordering = ("-upload_date",)
        db_table = "upload_history"

    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    upload_date = models.DateTimeField()
    r_package_version = models.CharField(max_length=50, null=True)
    generation_date = models.CharField(max_length=50, null=True)
    cdm_release_date = models.CharField(max_length=50, null=True)
    cdm_version = models.CharField(max_length=50, null=True)
    vocabulary_version = models.CharField(max_length=50, null=True)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Data Source: {self.data_source.name} - Upload Date: {self.upload_date}"


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
    min_value = models.BigIntegerField(null=True)
    max_value = models.BigIntegerField(null=True)
    avg_value = models.FloatField(null=True)
    stdev_value = models.FloatField(null=True)
    median_value = models.BigIntegerField(null=True)
    p10_value = models.BigIntegerField(null=True)
    p25_value = models.BigIntegerField(null=True)
    p75_value = models.BigIntegerField(null=True)
    p90_value = models.BigIntegerField(null=True)


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
    min_value = models.BigIntegerField(null=True)
    max_value = models.BigIntegerField(null=True)
    avg_value = models.FloatField(null=True)
    stdev_value = models.FloatField(null=True)
    median_value = models.BigIntegerField(null=True)
    p10_value = models.BigIntegerField(null=True)
    p25_value = models.BigIntegerField(null=True)
    p75_value = models.BigIntegerField(null=True)
    p90_value = models.BigIntegerField(null=True)
