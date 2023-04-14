# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-23 22:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_varkey_sync_with_sailthru'),
    ]

    operations = [
        migrations.AlterField(
            model_name='varkey',
            name='sync_with_sailthru',
            field=models.BooleanField(default=True, help_text='Sync this var with Sailthru; note that this will not have any retroactive effect if changing this flag on an existing var.'),
        ),
    ]