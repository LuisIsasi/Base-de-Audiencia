# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-27 22:45
from __future__ import unicode_literals

import core.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AudienceUser",
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
                    "email",
                    core.fields.NormalizedEmailField(
                        blank=True,
                        help_text="The person's email address; note that this field can be empty.",
                        max_length=500,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "email_hash",
                    models.CharField(
                        blank=True,
                        help_text="Sailthru's md5 hash of the email address.",
                        max_length=255,
                        null=True,
                    ),
                ),
                ("omeda_id", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "sailthru_id",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "vars",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default=dict
                    ),
                ),
            ],
            options={
                "get_latest_by": "modified",
                "abstract": False,
                "ordering": ("-modified", "-created"),
            },
        ),
        migrations.CreateModel(
            name="List",
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
                    "name",
                    models.CharField(
                        help_text="List name/description", max_length=500, unique=True
                    ),
                ),
                (
                    "slug",
                    core.fields.ListSlugField(
                        help_text="List slug: must be all-lowercase and underscore-separated",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("list", "List"), ("newsletter", "Newsletter")],
                        max_length=255,
                    ),
                ),
                (
                    "sync_externally",
                    models.BooleanField(
                        default=True,
                        help_text="Sync this list with external services, _eg_ Sailthru",
                    ),
                ),
                (
                    "archived",
                    models.BooleanField(
                        default=False,
                        help_text="Is the list active and should it be displayed to users?",
                    ),
                ),
            ],
            options={
                "ordering": ["slug"],
            },
        ),
        migrations.CreateModel(
            name="Product",
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
                    "name",
                    models.CharField(
                        help_text="Product name/description",
                        max_length=500,
                        unique=True,
                    ),
                ),
                (
                    "slug",
                    core.fields.ProductSlugField(
                        help_text="Product slug: must be all-lowercase and may optionally contain numbers",
                        max_length=500,
                        unique=True,
                    ),
                ),
                (
                    "brand",
                    models.CharField(
                        choices=[
                            ("Defense One", "Defense One"),
                            ("Govexec", "Govexec"),
                            ("Nextgov", "Nextgov"),
                            ("Route Fifty", "Route Fifty"),
                        ],
                        max_length=255,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("app", "App"),
                            ("asset", "Asset"),
                            ("event", "Event"),
                            ("questionnaire", "Questionnaire"),
                        ],
                        max_length=255,
                    ),
                ),
            ],
            options={
                "get_latest_by": "modified",
                "abstract": False,
                "ordering": ("-modified", "-created"),
            },
        ),
        migrations.CreateModel(
            name="ProductAction",
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
                ("timestamp", models.DateTimeField()),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("consumed", "consumed"),
                            ("registered", "registered"),
                        ],
                        max_length=255,
                    ),
                ),
                (
                    "audience_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_actions",
                        to="core.AudienceUser",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="core.Product",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="ProductActionDetail",
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
                ("description", models.TextField()),
                ("timestamp", models.DateTimeField()),
                (
                    "product_action",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="details",
                        to="core.ProductAction",
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="ProductSubtype",
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
                        help_text="Product subtype", max_length=1000, unique=True
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="ProductTopic",
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
                        help_text="Product topic", max_length=1000, unique=True
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Subscription",
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
                ("active", models.BooleanField(default=True)),
                (
                    "log_override",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON object containing values that supersede those that would otherwise be used when creating the on-save SubscriptionLog entry",
                    ),
                ),
                (
                    "audience_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="core.AudienceUser",
                    ),
                ),
                (
                    "list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="core.List",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SubscriptionLog",
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
                    "action",
                    models.CharField(
                        choices=[
                            ("subscribe", "subscribe"),
                            ("unsubscribe", "unsubscribe"),
                            ("update", "update"),
                        ],
                        max_length=255,
                    ),
                ),
                (
                    "comment",
                    models.TextField(
                        blank=True, help_text="Explanatory supporting text.", null=True
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "subscription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="log",
                        to="core.Subscription",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="SubscriptionTrigger",
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
                    "primary_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscription_triggers",
                        to="core.List",
                    ),
                ),
                (
                    "related_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="core.List",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserSource",
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
                        help_text="Slug-like value identifying the source of the user sign-up",
                        max_length=500,
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "audience_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_signups",
                        to="core.AudienceUser",
                    ),
                ),
            ],
            options={
                "ordering": ["timestamp"],
            },
        ),
        migrations.CreateModel(
            name="UserVarsHistory",
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
                    "vars",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, default=dict
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "audience_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vars_history",
                        to="core.AudienceUser",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddField(
            model_name="product",
            name="subtypes",
            field=models.ManyToManyField(to="core.ProductSubtype"),
        ),
        migrations.AddField(
            model_name="product",
            name="topics",
            field=models.ManyToManyField(to="core.ProductTopic"),
        ),
        migrations.AlterUniqueTogether(
            name="subscriptiontrigger",
            unique_together=set([("primary_list", "related_list")]),
        ),
        migrations.AlterUniqueTogether(
            name="subscription",
            unique_together=set([("audience_user", "list")]),
        ),
        migrations.AlterUniqueTogether(
            name="productaction",
            unique_together=set([("audience_user", "product", "type")]),
        ),
    ]
