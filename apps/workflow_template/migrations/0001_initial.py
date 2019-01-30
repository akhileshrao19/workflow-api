# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-01-30 13:39
from __future__ import unicode_literals

import django.contrib.postgres.fields.citext
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='template id')),
                ('name', django.contrib.postgres.fields.citext.CICharField(max_length=100)),
                ('template', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
    ]
