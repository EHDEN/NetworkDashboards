# Generated by Django 2.2.17 on 2021-06-15 18:28

import django.db.models.deletion
import uploader.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("uploader", "0011_country_alpha2"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadhistory",
            name="uploaded_file",
            field=models.FileField(
                null=True, upload_to=uploader.models.success_data_source_directory
            ),
        ),
        migrations.AlterField(
            model_name="datasource",
            name="hash",
            field=models.CharField(
                blank=True,
                default=uploader.models.hash_generator,
                max_length=255,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="uploadhistory",
            name="upload_date",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name="uploadhistory",
            name="pending_upload_id",
            field=models.IntegerField(
                help_text="The id of the PendingUpload record that originated this successful upload.",
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="PendingUpload",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("upload_date", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "Pending"),
                            (2, "Started"),
                            (3, "Canceled"),
                            (4, "Failed"),
                        ],
                        default=1,
                    ),
                ),
                (
                    "uploaded_file",
                    models.FileField(
                        upload_to=uploader.models.failure_data_source_directory
                    ),
                ),
                ("task_id", models.CharField(max_length=255, null=True)),
                (
                    "data_source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="uploader.DataSource",
                    ),
                ),
            ],
            options={
                "ordering": ("-upload_date",),
            },
        ),
        migrations.AlterField(
            model_name="achillesresults",
            name="data_source",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="uploader.DataSource"
            ),
        ),
        migrations.RemoveField(
            model_name="datasource",
            name="draft",
        ),
        migrations.RunSQL(
            "INSERT INTO achilles_results ("
            "    analysis_id,"
            "    stratum_1, stratum_2, stratum_3, stratum_4, stratum_5,"
            "    count_value,"
            "    min_value, max_value,"
            "    avg_value, stdev_value,"
            "    median_value,"
            "    p10_value, p25_value, p75_value, p90_value,"
            "    data_source_id"
            ") select "
            "    analysis_id,"
            "    stratum_1, stratum_2, stratum_3, stratum_4, stratum_5,"
            "    count_value,"
            "    min_value, max_value,"
            "    avg_value, stdev_value,"
            "    median_value,"
            "    p10_value, p25_value, p75_value, p90_value,"
            "    data_source_id "
            "from achilles_results_draft;"
        ),
        migrations.DeleteModel(
            name="AchillesResultsDraft",
        ),
    ]