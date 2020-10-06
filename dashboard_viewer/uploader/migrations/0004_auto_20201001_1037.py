# Generated by Django 2.2.16 on 2020-10-01 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("uploader", "0003_merge_20200923_1703"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datasource",
            name="release_date",
            field=models.DateField(
                help_text="Date at which DB is available for research for current release.",
                null=True,
            ),
        ),
    ]
