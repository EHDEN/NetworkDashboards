# Generated by Django 2.2.16 on 2020-10-02 11:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("uploader", "0004_auto_20201001_1037"),
    ]

    operations = [
        migrations.RenameField(
            model_name="uploadhistory",
            old_name="achilles_generation_date",
            new_name="generation_date",
        ),
        migrations.RenameField(
            model_name="uploadhistory",
            old_name="achilles_version",
            new_name="r_package_version",
        ),
    ]
