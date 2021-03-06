# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-31 18:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('login', models.CharField(max_length=255, unique=True)),
                ('username', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('password_salt', models.CharField(blank=True, max_length=255)),
                ('crypted_password', models.CharField(blank=True, max_length=255)),
                ('persistence_token', models.CharField(blank=True, max_length=255)),
                ('rights', models.IntegerField(default=1)),
            ],
            options={
                'db_table': 'users',
                'get_latest_by': 'created_at',
            },
        ),
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('achievement_number', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(db_index=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'achievements',
                'get_latest_by': 'created_at',
            },
        ),
        migrations.AlterUniqueTogether(
            name='achievement',
            unique_together=set([('user', 'achievement_number')]),
        ),
    ]
