# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-18 21:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160210_1216'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='usersource',
            options={'ordering': ['-timestamp']},
        ),
        migrations.AddField(
            model_name='subscriptiontrigger',
            name='override_previous_unsubscribes',
            field=models.BooleanField(default=False, help_text='Should this trigger ignore situations where the user has previously unsubscribed from the list in question? If checked, previously-unsubscribed users will be re-subscribed.'),
        ),
    ]
