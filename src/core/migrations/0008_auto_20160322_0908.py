# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 13:08
from __future__ import unicode_literals

from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations
from django.db.models import Q


def add_groups(apps, schema_editor):
    # Hacky way to ensure that permissions are added by this point. See:
    # https://code.djangoproject.com/ticket/23422
    emit_post_migrate_signal(verbosity=0, interactive=False, db=schema_editor.connection.alias)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    perms = Permission.objects.filter(
        Q(content_type__app_label="auth", content_type__model="group") |
        Q(content_type__app_label="auth", content_type__model="user") |
        Q(content_type__app_label="core")
    )
    group = Group.objects.create(name="Administrator")
    group.permissions.add(*perms)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Administrator").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20160223_1731'),
    ]

    operations = [
        migrations.RunPython(add_groups, remove_groups),
    ]