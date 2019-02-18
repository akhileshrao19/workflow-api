# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from apps.workflow_template.models import WorkflowTemplate


class WorkflowTemplateAdmin(admin.ModelAdmin):
    '''
    workflow template admin to be used with django admin app.
    '''
    list_display = ('id', 'name', 'structure', 'thumbnail')


admin.site.register(WorkflowTemplate, WorkflowTemplateAdmin)
