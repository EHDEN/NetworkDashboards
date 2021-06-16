# Generated by Django 2.2.17 on 2021-06-15 18:28

from django.db import migrations, models
import django.db.models.deletion
import uploader.models


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0011_country_alpha2'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadhistory',
            name='uploaded_file',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='hash',
            field=models.CharField(blank=True, default=uploader.models.hash_generator, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='uploadhistory',
            name='upload_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.CreateModel(
            name='PendingUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.IntegerField(choices=[(1, 'PENDING'), (2, 'STARTED'), (3, 'CANCELED'), (4, 'FAILED')], default=1)),
                ('uploaded_file', models.FileField(upload_to='')),
                ('task', models.IntegerField(null=True)),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uploader.DataSource')),
            ],
            options={
                'ordering': ('-upload_date',),
            },
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
