# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2020-09-03 13:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_auto_20200903_0331"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscriptionlog",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
