# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-19 16:35
from __future__ import unicode_literals

import core.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import sailthru_sync.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audienceuser',
            name='vars',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, validators=[core.fields.vars_jsonfield_validator, sailthru_sync.validators.reserved_words_jsonfield_validator]),
        ),
        migrations.AlterField(
            model_name='varkey',
            name='key',
            field=models.CharField(help_text='Var name (may not contain spaces)', max_length=500, unique=True, validators=[core.fields.varkey_validator, sailthru_sync.validators.reserved_words_validator]),
        ),
    ]