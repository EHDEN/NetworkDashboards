# Generated by Django 2.2.17 on 2021-07-21 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("uploader", "0012_auto_20210615_1828"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achillesresults",
            name="max_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="median_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="min_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="p10_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="p25_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="p75_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="p90_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="max_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="median_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="min_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="p10_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="p25_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="p75_value",
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name="achillesresultsarchive",
            name="p90_value",
            field=models.FloatField(null=True),
        ),
    ]
