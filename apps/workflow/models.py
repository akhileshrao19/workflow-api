# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta
import logging

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import CICharField
from django.db import models

from apps.common import constant as common_constant
from apps.workflow_template.models import WorkflowTemplate
from apps.company.models import UserCompany

User = get_user_model()

logger = logging.getLogger(__name__)


class Workflow(models.Model):
    '''
    Workflow model.
    '''
    template = models.ForeignKey(to=WorkflowTemplate, on_delete=models.PROTECT)
    name = CICharField(max_length=256)
    creator = models.ForeignKey(to=UserCompany, on_delete=models.PROTECT)
    start_at = models.DateTimeField()
    complete_at = models.DateTimeField(
        null=True,
        help_text='time when workflow completed'
    )
    duration = models.DurationField(
        default=timedelta(0),
        help_text='expected completion duration'
    )

    def __unicode__(self):
        return '{workflow_name}-#-{creator}'.format(
            workflow_name=self.name,
            creator=self.creator_id
        )

    def send_mail(self, is_updated):
        '''
        send workflow created/updated mail.
        '''
        context = {
            'name': self.creator.user.name,
            'workflow_name': self.name,
            'write_permission': True,
            'is_updated': is_updated,
            'is_creator': True
        }
        self.creator.user.email_user(
            'workflow.txt',
            'workflow.html',
            'Workflow Update',
            context
        )
        logger.info('Workflow create/update mail send to {email}'.format(
            email=self.creator.user.email))


class Task(models.Model):
    '''
    Tasks in workflows.
    '''
    workflow = models.ForeignKey(
        to=Workflow, on_delete=models.CASCADE, related_name='tasks')
    title = CICharField(max_length=256)
    description = models.TextField(blank=True, default='')
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        related_name='child'
    )
    assignee = models.ForeignKey(
        UserCompany,
        on_delete=models.PROTECT,
        related_name='tasks'
    )
    completed_at = models.DateTimeField(null=True)
    start_delta = models.DurationField(
        default=timedelta(0),
        help_text='time delay between completion of parent task and star of current task'
    )
    status = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.TASK_STATUS,
            common_constant.TASK_STATUS._fields
        )),
        default=common_constant.TASK_STATUS.UPCOMMING
    )

    def __unicode__(self):
        return '{workflow_id}-#-{title}'.format(
            title=self.title,
            workflow_id=self.workflow_id
        )

    def send_mail(self, is_new):
        '''
        send new/update task mail.
        '''
        context = {
            'task_title': self.title,
            'workflow_name': self.workflow.name,
            'name': self.assignee.user.name,
            'is_new': is_new
        }
        self.assignee.user.email_user(
            'task.txt',
            'task.html',
            'Task Update',
            context
        )
        logger.info('Task new/update mail send to {email}'.format(
            email=self.assignee.user.email))


class WorkflowAccess(models.Model):
    '''
    Workflow accees permissions.
    '''
    employee = models.ForeignKey(
        UserCompany, on_delete=models.CASCADE, related_name='shared_workflows')
    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name='accessors')
    permission = models.PositiveIntegerField(
        choices=(choice for choice in zip(
            common_constant.PERMISSION,
            common_constant.PERMISSION._fields
        )),
        default=common_constant.PERMISSION.READ
    )

    class Meta:
        unique_together = ('employee', 'workflow')

    def __unicode__(self):
        return '{employee_id}-#-{workflow_id}-#-{permission}'.format(
            employee_id=self.employee_id,
            workflow_id=self.workflow_id,
            permission=self.permission
        )

    def send_mail(self, is_updated):
        '''
        send workflow share/update mail.
        '''
        context = {
            'name': self.employee.user.name,
            'workflow_name': self.workflow.name,
            'write_permission': self.permission == common_constant.PERMISSION.READ_WRITE,
            'is_updated': is_updated,
            'is_creator': False
        }
        self.employee.user.email_user(
            'workflow.txt',
            'workflow.html',
            'Workflow Update',
            context
        )
        logger.info('Workflow share/update mail send to {email}'.format(
            email=self.employee.user.email))
