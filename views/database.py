from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, functions


def overview(request):
    TableForm = forms.get_dialect_form('TableForm', 
        functions.get_conn_params(request)['dialect'])
    params = request.GET
    supported_engines = functions.common_query(request, 'supported_engines')
    charset_list = functions.common_query(request, 'charset_list')
    existing_tables = functions.rpr_query(request, 'existing_tables')
    # table deletion or emptying request catching and handling
    if request.method == 'POST' and request.GET.get('update'):
        l = request.POST.get('whereToEdit').strip().split(';');
        conditions = functions.get_conditions(l)
        q = ''
        if request.GET.get('update') == 'drop':
            q = 'drop_table'
        elif request.GET.get('update') == 'empty':
            q = 'empty_table'
        query_data = {'db':request.GET['database'],'conditions':functions.get_conditions(l)}
        if request.GET.get('schema'):
            query_data['schema'] = request.GET.get('schema')
        return functions.rpr_query(request, q , query_data)
        
    
    if request.method == 'POST':
        p = request.POST
        sub_form_count = 0
        for fi in p:
            if len( fi.split('_') ) == 2:
                if sub_form_count < int(fi.split('_')[1]):
                    sub_form_count = int(fi.split('_')[1])
        form = TableForm(engines=supported_engines, charsets=charset_list, data=request.POST,
            sub_form_count=(sub_form_count+1), existing_tables=existing_tables)
        if form.is_valid():
            query_data = {'sub_form_count':(sub_form_count+1), 'db': request.GET['database']}
            query_data.update(form.cleaned_data)
            return functions.rpr_query(request, 'create_table',
                query_data)
        else:
            return functions.response_shortcut(request, template='form_errors',
                extra_vars={'form':form,})
    else:
        form = TableForm(engines=supported_engines, charsets=charset_list
            , label_suffix=' ->', existing_tables=existing_tables)
            

    return functions.response_shortcut(request, extra_vars={'form': form, 'edit':False,
        'table_fields': ['name', 'engine', 'charset', 'inherit', 'of_type'],
        'odd_fields': ['type','key','charset',]}
    )
    

def query(request):
    pass


def import_(request):
    pass


def export(request):
    pass

def route(request):
    if request.GET['view'] == 'overview':
        return overview(request)
    elif request.GET['view'] == 'query':
        return query(request)
    elif request.GET['view'] == 'import':
        return import_(request)
    elif request.GET['view'] == 'export':
        return export(request)
    

