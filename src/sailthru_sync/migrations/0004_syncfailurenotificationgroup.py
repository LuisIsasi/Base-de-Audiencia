# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-20 15:08
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ("djcelery", "0001_initial"),
        ("auth", "0007_alter_validators_add_error_messages"),
        ("sailthru_sync", "0003_auto_20160419_1716"),
    ]

    operations = [
        migrations.CreateModel(
            name="SyncFailureNotificationGroup",
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
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                (
                    "interested_errors",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=5),
                        blank=True,
                        default=[],
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "interested_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="auth.Group"
                    ),
                ),
                (
                    "notification_task",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="djcelery.PeriodicTask",
                    ),
                ),
            ],
            options={
                "get_latest_by": "modified",
                "ordering": ("-modified", "-created"),
                "abstract": False,
            },
        ),
    ]
