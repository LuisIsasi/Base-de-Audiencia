# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2020-09-03 07:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_auto_20200824_1240"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscriptionlog",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
