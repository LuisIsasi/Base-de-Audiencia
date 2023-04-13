import json

from celery.result import AsyncResult
from django import shortcuts as dj_shortcuts
from django.http import HttpResponse
from django.views.decorators import csrf, http

from .models import TestQuestionnaire
from .tasks import return_noodles


def questionnaire_detail(request, pk):
    q = dj_shortcuts.get_object_or_404(TestQuestionnaire, pk=int(pk))
    context = {
        'questionnaire': q,
    }
    return dj_shortcuts.render(request, 'example_tests/testquestionnaire.html', context=context)


@csrf.csrf_exempt
def request_noodles(request):
    result = return_noodles.delay()
    return HttpResponse(json.dumps({"task_id": result.task_id}), content_type="application/json")


@http.require_GET
def check_noodles(request):
    task_id = request.GET.get("task_id")
    data = {
        'ready': False,
    }
    if AsyncResult(task_id).ready():
        data['ready'] = True

    return HttpResponse(json.dumps(data), content_type="application/json")
