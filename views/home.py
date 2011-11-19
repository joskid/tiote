from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods
from django.forms.formsets import formset_factory

from tiote import forms, functions


def home(request):
    params = request.GET
    DbForm = forms.get_dialect_form('DbForm', 
        functions.get_conn_params(request)['dialect']
    )
    template_list = functions.common_query(request, 'template_list')
    user_list = functions.common_query(request, 'user_list');
    charset_list = functions.common_query(request, 'charset_list');
    if request.method == 'POST':
        form = DbForm(templates=template_list, users=user_list,
            charsets=charset_list, data=request.POST)
        if form.is_valid():
            return functions.rpr_query(request, 'create_db', form.cleaned_data)
    else:
        form = DbForm(templates=template_list, users=user_list, charsets=charset_list)
        
    return functions.response_shortcut(request,
        extra_vars={'form':form, 'variables':functions.get_home_variables(request)})


def users(request):
    params = request.GET
    conn_params = functions.get_conn_params(request)
    db_list = functions.common_query(request, 'db_list')
    group_list = functions.common_query(request, 'group_list')
    UserForm = forms.get_dialect_form('UserForm', conn_params['dialect'] )
    # user deletion request handling
    if request.method == 'POST' and request.GET.get('update') == 'delete':
        l = request.POST.get('whereToEdit').strip().split(';');
        conditions = functions.get_conditions(l)
        return functions.rpr_query(request, 'drop_user', conditions)
    # user creation and editing request handling
    if request.method == 'POST' and not request.GET.get('sub-view'):
        form = UserForm(dbs=db_list, groups=group_list, data=request.POST)
        if form.is_valid():
            if conn_params['dialect'] == 'postgresql':
                # query determination and submission
                if not request.GET.get('subview'): # new user creation
                    return functions.rpr_query(request,
                        'create_user', form.cleaned_data)
                return HttpResponse('valid form submitted!')
            
            elif conn_params['dialect'] == 'mysql':
                # some necessary checks
                if form.cleaned_data['access'] == 'select' and not form.cleaned_data['select_databases']:
                    return HttpResponse('The submitted form is incomplete! No databases selected!')
                if form.cleaned_data['privileges'] == 'select':
                    if not form.cleaned_data['user_privileges'] and not form.cleaned_data['administrator_privileges']:
                        return HttpResponse('The submitted form is incomplete! No privileges selected!')
                # query determination and submission
                if not request.GET.get('subview'): # new user creation
                    return functions.rpr_query(request,
                        'create_user', form.cleaned_data)
                return HttpResponse('valid form submitted!')
        else:
            h = functions.response_shortcut(request,template='form_errors',
                extra_vars={'form':form});
            h.set_cookie('tt_formContainsErrors','true')
            return h
            
    elif request.method == 'POST' and request.GET.get('view'):
        return HttpResponse('edit not yet implemented')
    else:
        form = UserForm(dbs=db_list, groups=group_list)

    return functions.response_shortcut(request, extra_vars={'form':form,})


def query(request):
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented')
    
    else:
        form = forms.QueryForm()
        
    return functions.response_shortcut(request, extra_vars={'form':form,})    
    
def import_(request):
    if request.method == 'POST':
        form = forms.ImportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented');
    
    else:
        form = forms.ImportForm()
    
    return functions.response_shortcut(request, extra_vars={'form':form,})


def export(request):
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented');
    
    else:
        form = forms.ExportForm()
        
    return functions.response_shortcut(request, extra_vars={'form':form,})


def route(request):
    if request.GET['view'] == 'users':
        return users(request)
    elif request.GET['view'] == 'query':
        return query(request)
    elif request.GET['view'] == 'export':
        return export(request)
    elif request.GET['view'] == 'import':
        return import_(request)
    elif request.GET['view'] == 'home':
        return home(request)
    
