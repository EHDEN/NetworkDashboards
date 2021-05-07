from rest_framework import serializers

from .models import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        exclude = ("hash",)
