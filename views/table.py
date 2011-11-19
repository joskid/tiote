from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, functions


def browse(request):
    # row(s) deletion request handling
    if request.method == 'POST' and request.GET.get('update') == 'delete':
        # might be needed for future corrections
#        l = request.POST.get('whereToEdit').strip().split(';');
#        conditions = functions.get_conditions(l)
        conditions = [functions.construct_cond(item[0], item[1]) 
            for item in functions.dict_conds(request.POST.get('whereToEdit')) ]
        query_data = {'database': request.GET.get('database'),'table': request.GET.get('table'),
             'conditions': conditions}
        if request.GET.get('schema'):
            query_data['schema'] = request.GET.get('schema')
        return functions.rpr_query(request, 'delete_row', query_data)
    # row(s) edit/updating request handling
    elif request.method == 'POST' and request.GET.get('update') == 'edit':
        return functions.http_500('feature not yet implemented!')
    
    return functions.response_shortcut(request)


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

def route(request):
    if request.GET.get('view') == 'browse':
        return browse(request)
    elif request.GET.get('view') == 'structure':
        return structure(request)
    elif request.GET.get('view') == 'import':
        return import_(request)
    elif request.GET.get('view') == 'export':
        return export(request)
    else:
        return http_500('malformed URL')