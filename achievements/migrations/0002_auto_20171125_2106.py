# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-25 14:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('achievements', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievement',
            name='icon_path',
            field=models.CharField(blank=True, default=None, max_length=255),
        ),
    ]
