# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-19 05:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TesterStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'checker_statuses',
                'get_latest_by': 'updated_at',
            },
        ),
    ]
