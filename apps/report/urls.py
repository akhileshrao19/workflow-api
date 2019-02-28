from django.conf.urls import url

from rest_framework import routers

from apps.report.views import IJLEmployeeCount, EmployeeReport, WorkflowReport

router = routers.SimpleRouter()

urlpatterns = router.urls

urlpatterns += [
    url(r'^ijl-employees', IJLEmployeeCount.as_view(), name='ijl-employees'),
    url(r'^employee-report/(?P<pk>[0-9]+)/$', EmployeeReport.as_view(), name='employee-report'),
    url(r'^workflow-report/(?P<pk>[0-9]+)/$', WorkflowReport.as_view(), name='workflow-report'),
]
