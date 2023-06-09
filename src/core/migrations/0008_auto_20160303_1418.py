# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-03 19:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_auto_20160223_1731"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailChangeAudienceUser",
            fields=[],
            options={
                "proxy": True,
                "verbose_name_plural": "users - change emails",
                "verbose_name": "user email",
            },
            bases=("core.audienceuser",),
        ),
        migrations.AlterField(
            model_name="audienceuser",
            name="omeda_id",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Omeda ID"
            ),
        ),
    ]
