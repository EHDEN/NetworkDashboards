
from django.db import models
from django.db.models.signals import post_save, post_delete


CONTINENTS = [
    ('AF', 'Africa'),
    ('AS', 'Asia'),
    ('EU', 'Europe'),
    ('NA', 'North America'),
    ('OC', 'Oceania'),
    ('SA', 'South America'),
    ('AN', 'Antarctica'),
]


class Continent(models.Model):
    continent = models.CharField(max_length=40)


class Country(models.Model):
    country   = models.CharField(max_length=40)
    #continent = models.CharField(max_length=2, choices=CONTINENTS)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)


class Location(models.Model):
    city    = models.CharField(max_length=40)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.city} - {self.country.country} - {self.country.continent}"


class DatabaseType(models.Model):
    type = models.CharField(max_length=40)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.type


class Sources(models.Model):
    class Meta:
        db_table = "achilles_datasources"

    name                     = models.CharField(max_length=40)
    release_date             = models.DateField(
        help_text="Date at which DB is available for research for current release"
    )
    database_type            = models.ForeignKey(DatabaseType, on_delete=models.SET_NULL, null=True)
    location                 = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    latitude                 = models.FloatField()
    longitude                = models.FloatField()
    link                     = models.URLField()


def after_source_saved(sender, **kwargs):
    """
    TODO After a source is inserted dashboards on superset might need to be updated
    """
    pass


post_save.connect(after_source_saved, sender=Sources)


def after_source_deleted(sender, **kwargs):
    """
    TODO After a source is deleted dashboards on superset might need to be updated
    """
    pass


post_delete.connect(after_source_deleted, sender=Sources)


class UploadHistory(models.Model):
    source                   = models.ForeignKey(Sources, on_delete=models.CASCADE)
    date                     = models.DateField()
    achilles_version         = models.CharField(max_length=10)
    achilles_generation_date = models.DateField()
    cdm_version              = models.CharField(max_length=10)
    vocabulary_version       = models.CharField(max_length=10)


class AchillesResults(models.Model):
    class Meta:
        db_table = "achilles_results"
        indexes = [
            models.Index(fields=("source",)),
            models.Index(fields=("analysis_id",))
        ]

    source      = models.ForeignKey(Sources, on_delete=models.CASCADE)
    analysis_id = models.BigIntegerField()
    stratum_1   = models.TextField()
    stratum_2   = models.TextField()
    stratum_3   = models.TextField()
    stratum_4   = models.TextField()
    stratum_5   = models.TextField()
    count_value = models.BigIntegerField()


class AchillesResultsArchive(models.Model):
    class Meta:
        db_table = "achilles_results_archive"
        indexes = [
            models.Index(fields=("source",)),
            models.Index(fields=("analysis_id",))
        ]

    date        = models.DateField()
    upload_id   = models.ForeignKey(UploadHistory, on_delete=models.CASCADE)
    source      = models.ForeignKey(Sources, on_delete=models.CASCADE)
    analysis_id = models.BigIntegerField()
    stratum_1   = models.TextField()
    stratum_2   = models.TextField()
    stratum_3   = models.TextField()
    stratum_4   = models.TextField()
    stratum_5   = models.TextField()
    count_value = models.BigIntegerField()


