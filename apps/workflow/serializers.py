# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from apps.common import constant as common_constant
from apps.company.models import UserCompany
from apps.company.serializers import UserCompanySerializer
from apps.workflow.models import Workflow, Task, WorkflowAccess
from apps.workflow_template.models import WorkflowTemplate
from apps.workflow_template.serializers import WorkflowTemplateBaseSerializer as WorkflowTemplateBaseSerializer


class TaskBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'workflow', 'title', 'description', 'parent_task',
                  'assignee', 'completed_at', 'start_delta', 'status')
        read_only_fields = ('id', 'workflow', 'parent_task', 'completed_at', 'status')


class WorkflowAccessBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAccess
        fields = ('id', 'employee', 'permission')
        read_only_fields = ('id', )


class WorkflowAccessCreateSerializer(WorkflowAccessBaseSerializer):
    def validate(self, data):
        """
        checks that admin, employee and workflow belongs to the same company.
        """
        if not data['workflow'].creator.company == self.context['request'].user.company:
            raise serializers.ValidationError('workflow does not belong to your company')
        if not data['employee'].company == data['workflow'].creator.company:
            raise serializers.ValidationError('Employee must be of the same company')
        return data

    def create(self, validated_data):
        '''
        overrided to send mail after creating new accessor.
        '''

        instance = super(WorkflowAccessCreateSerializer, self).create(validated_data)
        instance.send_mail()
        return instance

    class Meta(WorkflowAccessBaseSerializer.Meta):
        fields = WorkflowAccessBaseSerializer.Meta.fields + ('workflow',)


class WorkflowAccessUpdateSerializer(WorkflowAccessCreateSerializer):
    def validate(self, data):
        return data

    def update(self, instance, validated_data):
        '''
        override to send mail after update.
        '''
        instance = super(WorkflowAccessUpdateSerializer, self).update(instance, validated_data)
        instance.send_mail()
        return instance

    class Meta(WorkflowAccessCreateSerializer.Meta):
        read_only_fields = WorkflowAccessCreateSerializer.Meta.read_only_fields + ('workflow', 'employee')


class WorkflowBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('id', 'template', 'name', 'creator', 'start_at', 'complete_at', 'duration')
        read_only_fields = ('id', 'creator', 'complete_at')


class WorkflowCreateSerializer(WorkflowBaseSerializer):
    tasks = TaskBaseSerializer(many=True)
    accessors = WorkflowAccessBaseSerializer(many=True)

    def create(self, validated_data):
        '''
        override due to nested writes

        Arguments:
            validated_data {dict} -- data recieved after validation
        '''

        tasks = validated_data.pop('tasks', [])
        accessors = validated_data.pop('accessors', [])

        employee = self.context['request'].user.active_employee
        people_assiciated = {}
        people_assiciated[employee.id] = {
            'employee': employee,
            'is_creator': True
        }

        workflow = Workflow.objects.create(creator=employee, **validated_data)

        if tasks:
            prev_task = None
            for task in tasks:
                prev_task = Task.objects.create(workflow=workflow, parent_task=prev_task, **task)

                person = people_assiciated.get(prev_task.assignee_id, {})
                if not person:
                    person['employee'] = prev_task.assignee
                    people_assiciated[prev_task.assignee_id] = person
                if not person.get('task_list', None):
                    person['task_list'] = []
                person['task_list'].append(prev_task.title)

        if accessors:
            for accessor in accessors:
                if accessor.get('employee').id == employee.id:
                    # do not add creator in the accessor list.
                    continue

                instance = WorkflowAccess.objects.create(workflow=workflow, **accessor)

                person = people_assiciated.get(instance.employee_id, {})
                if not person:
                    person['employee'] = instance.employee
                    people_assiciated[instance.employee_id] = person
                person['is_shared'] = True
                person['write_permission'] = instance.permission == common_constant.PERMISSION.READ_WRITE

        workflow.send_mail(people_assiciated, is_updated=False)

        return workflow

    class Meta(WorkflowBaseSerializer.Meta):
        fields = WorkflowBaseSerializer.Meta.fields + ('tasks', 'accessors')


class WorkflowUpdateSerializer(WorkflowBaseSerializer):
    '''
    Serializer for updating workflow and its tasks. Accessors are not removed via this.
    '''

    def update(self, instance, validated_data):
        '''
        override due to sending mails on update
        '''
        instance = super(WorkflowUpdateSerializer, self).update(instance, validated_data)

        people_assiciated = {}
        people_assiciated[instance.creator_id] = {'employee': instance.creator}

        print instance.tasks

        for accessor in instance.accessors.all():
            people_assiciated[accessor.employee_id] = {'employee': accessor.employee}
        for task in instance.tasks.all():
            people_assiciated[task.assignee_id] = {'employee': task.assignee}
        instance.send_mail(people_assiciated, is_updated=True)

        return instance

    class Meta(WorkflowBaseSerializer.Meta):
        read_only_fields = WorkflowBaseSerializer.Meta.read_only_fields + ('template',)


class TaskUpdateSerializer(TaskBaseSerializer):
    def update(self, instance, validated_data):
        employee = self.context['request'].user.active_employee
        # don't update assignee if user is only assignee and not admin or write accessor
        isOnlyAssignee = instance.assignee == employee and not employee.is_admin
        isOnlyAssignee = isOnlyAssignee and (not employee.shared_workflows.filter(
            workflow=instance,
            permission=common_constant.PERMISSION.READ_WRITE
        ).exists())
        if isOnlyAssignee:
            validated_data.pop('assignee', None)

        instance = super(TaskUpdateSerializer, self).update(instance, validated_data)
        instance.send_mail()

        return instance

    class Meta(TaskBaseSerializer.Meta):
        pass
