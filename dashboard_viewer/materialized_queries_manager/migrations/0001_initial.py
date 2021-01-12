# Generated by Django 2.2.17 on 2021-01-12 16:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MaterializedQuery',
            fields=[
                ('matviewname', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.RegexValidator('^[_0-9a-zA-Z]+$', 'Only alphanumeric characters and the character "_" are allowed.')])),
                ('definition', models.TextField(validators=[django.core.validators.RegexValidator('--', 'Single line comments are not allowed', inverse_match=True), django.core.validators.RegexValidator('/\\*.*?\\*/', 'Block comments are not allowed', inverse_match=True)])),
            ],
            options={
                'db_table': 'pg_matviews',
                'managed': False,
            },
        ),
    ]
