import json

from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods
from django.forms.formsets import formset_factory

from tiote import forms, utils


def home(request):
    conn_params = utils.fns.get_conn_params
    # queries and initializations
    template_list = utils.db.common_query(request, 'template_list')
    user_list = utils.db.common_query(request, 'user_list');
    charset_list = utils.db.common_query(request, 'charset_list');
    
    DbForm = forms.get_dialect_form('DbForm', 
        utils.fns.get_conn_params(request)['dialect']
    )
    
    if request.method == 'POST':
        form = DbForm(templates=template_list, users=user_list,
            charsets=charset_list, data=request.POST)
        if form.is_valid():
            return utils.db.rpr_query(conn_params, 'create_db', form.cleaned_data)
    else:
        form = DbForm(templates=template_list, users=user_list, charsets=charset_list)
        
    return utils.fns.response_shortcut(request,
        extra_vars={'form':form, 'variables':utils.db.get_home_variables(request)}
    )



def users(request):
    # queries and intializations
    conn_params = utils.fns.get_conn_params(request)
    db_list = utils.db.common_query(request, 'db_list')
    group_list = utils.db.common_query(request, 'group_list')
    UserForm = forms.get_dialect_form('UserForm', conn_params['dialect'] )
    # user deletion request handling
    if request.method == 'POST' and request.GET.get('update') == 'delete':
        l = request.POST.get('whereToEdit').strip().split(';');
        conditions = utils.fns.get_conditions(l)
        return utils.db.rpr_query(request, 'drop_user', conditions)
    # user creation and editing request handling
    if request.method == 'POST' and not request.GET.get('sub-view'):
        form = UserForm(dbs=db_list, groups=group_list, data=request.POST)
        if form.is_valid():
            if conn_params['dialect'] == 'postgresql':
                # query determination and submission
                if not request.GET.get('subview'): # new user creation
                    return utils.db.rpr_query(conn_params, 'create_user', form.cleaned_data)
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
                    return utils.db.rpr_query(conn_params, 'create_user', form.cleaned_data)
                return HttpResponse('valid form submitted!')
        else:
            h = utils.fns.response_shortcut(request,template='form_errors', extra_vars={'form':form});
            h.set_cookie('tt_formContainsErrors','true')
            return h
            
    elif request.method == 'POST' and request.GET.get('v'):
        return HttpResponse('edit not yet implemented')
    else:
        form = UserForm(dbs=db_list, groups=group_list)

    return utils.fns.response_shortcut(request, extra_vars={'form':form,})


def query(request):
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented')
    
    else:
        form = forms.QueryForm()
        
    return utils.fns.response_shortcut(request, extra_vars={'form':form,})    
    
def import_(request):
    if request.method == 'POST':
        form = forms.ImportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented');
    
    else:
        form = forms.ImportForm()
    
    return utils.fns.response_shortcut(request, extra_vars={'form':form,})


def export(request):
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented');
    
    else:
        form = forms.ExportForm()
        
    return utils.fns.response_shortcut(request, extra_vars={'form':form,})


def route(request):
    if request.GET['v'] == 'users':
        return users(request)
    elif request.GET['v'] == 'query':
        return query(request)
    elif request.GET['v'] == 'export':
        return export(request)
    elif request.GET['v'] == 'import':
        return import_(request)
    elif request.GET['v'] == 'home':
        return home(request)
    
