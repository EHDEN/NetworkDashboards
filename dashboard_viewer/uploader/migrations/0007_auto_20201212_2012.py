# Generated by Django 2.2.17 on 2020-12-12 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("uploader", "0006_auto_20201109_2152"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uploadhistory",
            name="vocabulary_version",
            field=models.CharField(max_length=50),
        ),
    ]