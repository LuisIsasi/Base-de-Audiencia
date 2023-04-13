from django.conf.urls import url

from . import views

app_name = 'example_tests'
urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/$', views.questionnaire_detail, name='q-detail'),
    url(r'^request-noodles/$', views.request_noodles, name='q-request-noodles'),
    url(r'^check-noodles/$', views.check_noodles, name='q-check-noodles'),
]
