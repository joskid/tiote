from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, functions


def ajax(request):
    return functions.http_500('feature not yet implemented!')


def browse(request):
    pass


def structure(request):
    pass



def insert(request):
    pass


def edit(request):
    pass



def import_(request):
    pass


def export(request):
    pass