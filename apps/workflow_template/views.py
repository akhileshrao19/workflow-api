# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
import logging

from django.contrib.auth import get_user_model

from rest_framework import viewsets, mixins
from rest_framework import response, status
from apps.common import constant as common_constant
from apps.company.permissions import IsActiveCompanyAdmin
from apps.workflow_template.models import WorkflowTemplate
from apps.workflow_template.serializers import WorkflowTemplateSerializer


class TemplateListRetrieveView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = (IsActiveCompanyAdmin,)
