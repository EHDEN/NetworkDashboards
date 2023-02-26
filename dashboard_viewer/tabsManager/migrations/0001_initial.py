# Generated by Django 2.2.7 on 2020-01-25 12:07

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tab",
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
                (
                    "title",
                    models.CharField(
                        help_text="Text to appear on the tab under the icon",
                        max_length=30,
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        help_text="Font awesome icon v4. Just the end part, e.g. fa-clock-o -> clock-o",
                        max_length=20,
                    ),
                ),
                ("url", models.URLField()),
                ("position", models.PositiveIntegerField()),
                (
                    "visible",
                    models.BooleanField(help_text="If the tab should be displayed"),
                ),
            ],
        ),
    ]
