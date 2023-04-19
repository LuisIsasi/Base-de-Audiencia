# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-19 21:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sailthru_sync", "0002_auto_20160330_1140"),
    ]

    operations = [
        migrations.AddField(
            model_name="syncfailure",
            name="acknowledged",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="syncfailure",
            name="resolved",
            field=models.BooleanField(default=False),
        ),
    ]
