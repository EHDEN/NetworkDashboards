
from django.db import models


class Country(models.Model):
    city = models.TextField


class City(models.Model):
    city    = models.TextField
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class Location(models.Model):
    latitude  = models.FloatField()
    longitude = models.FloatField()
    city      = models.ForeignKey(City, on_delete=models.CASCADE)


class DatabaseType(models.Model):
    type = models.TextField()


class Sources(models.Model):
    name                     = models.TextField()
    release_date             = models.DateField()  # Date at which DB is available for research for current release
    achilles_version         = models.CharField(max_length=10)
    achilles_generation_date = models.DateField()
    cdm_version              = models.CharField(max_length=10)
    vocabulary_version       = models.CharField(max_length=10)
    database_type            = models.ForeignKey(DatabaseType, on_delete=models.SET_NULL, null=True)
    location                 = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    link                     = models.URLField()


class AchillesResults(models.Model):
    class Meta:
        db_table = "AchillesResults"

    source      = models.ForeignKey(Sources, on_delete=models.CASCADE)
    analysis_id = models.BigIntegerField()
    stratum_1   = models.TextField()
    stratum_2   = models.TextField()
    stratum_3   = models.TextField()
    stratum_4   = models.TextField()
    stratum_5   = models.TextField()
    count_value = models.BigIntegerField()


class UpdateHistory(models.Model):
    source = models.ForeignKey(Sources, on_delete=models.CASCADE)
    date = models.DateField()
