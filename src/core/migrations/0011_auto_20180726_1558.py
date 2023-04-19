# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2018-07-26 19:58
from __future__ import unicode_literals

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_auto_20160419_1235"),
    ]

    operations = [
        migrations.CreateModel(
            name="AthenaContentMetadata",
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
                ("athena_content_id", models.IntegerField(db_index=True, unique=True)),
                (
                    "date_published",
                    models.DateTimeField(
                        help_text="The date and time the post went live.",
                        null=True,
                        verbose_name="Publish date",
                    ),
                ),
                (
                    "date_created",
                    models.DateTimeField(
                        help_text="This date the original post was created in the govexec database."
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                (
                    "slug",
                    models.SlugField(
                        help_text="The URL name of the content, based off title.",
                        max_length=255,
                    ),
                ),
                (
                    "absolute_url",
                    models.URLField(max_length=500, verbose_name="Absolute URL"),
                ),
                (
                    "canonical_url",
                    models.URLField(
                        blank=True,
                        max_length=500,
                        null=True,
                        verbose_name="Canonical URL",
                    ),
                ),
                ("site_name", models.CharField(max_length=25)),
                (
                    "organization",
                    models.SlugField(
                        help_text="The URL name of the organization associated with the content.",
                        max_length=255,
                    ),
                ),
                (
                    "authors",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=200),
                        blank=True,
                        help_text="The author(s) associated with the content.",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "categories",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        default=dict,
                        help_text="The primary category slug and slugs for any secondary categories associated with the content.",
                    ),
                ),
                (
                    "topics",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=75),
                        blank=True,
                        help_text="The topic slugs associated with the content.",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "keywords",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=100),
                        blank=True,
                        help_text="The keywords associated with the content. The same keyword may also exist in the interests field.",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "interests",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=100),
                        blank=True,
                        help_text="The (sailthru) interests associated with the content. The same interest may also exist in the keywords field.",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "is_sponsored_content",
                    models.BooleanField(
                        default=False,
                        help_text="Signifies whether the content is associated with a primary category that is a sponsored category.\n                     Note: This is not the same as the is_sponsored field in govexec.post_manager_content. It is the return\n                     value of the is_sponsored_content method in the post_manager.Content class in the govexec codebase.",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Athena Content Metadata",
            },
        ),
        migrations.CreateModel(
            name="AthenaContentType",
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
                    "name",
                    models.CharField(
                        help_text="This is the combination of the app label and model name from the govexec.django_content_type table. E.g. post_manager.post",
                        max_length=200,
                        unique=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UserContentHistory",
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
                ("email", models.EmailField(db_index=True, max_length=500)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("referrer", models.URLField(null=True)),
                (
                    "athena_content_metadata",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="user_content_history",
                        to="core.AthenaContentMetadata",
                        to_field="athena_content_id",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "User Content History",
            },
        ),
        migrations.AddField(
            model_name="athenacontentmetadata",
            name="athena_content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="athena_content_metadata",
                to="core.AthenaContentType",
            ),
        ),
    ]
