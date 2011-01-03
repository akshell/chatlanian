# (c) 2010-2011 by Anton Korenyushkin

from httplib import INTERNAL_SERVER_ERROR

from django.http import HttpResponse
from sentry.models import GroupedMessage

from utils import read_file
from paths import ROOT


def pingdom_view(request):
    if read_file(ROOT.log):
        return HttpResponse('patsak', status=INTERNAL_SERVER_ERROR)
    if GroupedMessage.objects.filter(status=0).count():
        return HttpResponse('chatlanian', status=INTERNAL_SERVER_ERROR)
    return HttpResponse('OK')
