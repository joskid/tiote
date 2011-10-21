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
    if request.method == 'POST':
        form = DbForm(templates=template_list, data=request.POST)
        if form.is_valid():
            pass
    else:
        form = DbForm(templates=template_list)
        
    c = {'form':form, 'variables':functions.get_home_variables(request)}
    template = functions.skeleton(params['view'])
    context = RequestContext(request, {
        }, [functions.site_proc]                          
    )
    context.update(c)
    return HttpResponse(template.render(context))


def users(request):
    def get_conditions(l):
        conditions = []
        for i in range( len(l) ):
            ll = l[i].strip().split('AND')
            d = {}
            for ii in range( len(ll) ):
                lll = ll[ii].strip().split('=')
                d.update( {lll[0].lower() : lll[1].lower()} )
            conditions.append(d)
        return conditions
            
    params = request.GET
    conn_params = functions.get_conn_params(request)
    db_list = functions.common_query(request, 'db_list')
    group_list = functions.common_query(request, 'group_list')
    UserForm = forms.get_dialect_form('UserForm', conn_params['dialect'] )
    # user deletion request handling
    if request.method == 'POST' and request.GET.get('update') == 'delete':
        l = request.POST.get('whereToEdit').strip().split(';');
        conditions = get_conditions(l)
        return functions.rpr_query(request, 'drop_user', conditions)
    # user creation and editing request handling
    if request.method == 'POST' and not request.GET.get('sub-view'):
        form = UserForm(dbs=db_list,data=request.POST, groups=group_list)
        if form.is_valid():
            if conn_params['dialect'] == 'postgresql':
                assert False
            # some necessary checks
            elif conn_params['dialect'] == 'mysql':
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
    elif request.method == 'POST' and request.GET.get('view'):
        return HttpResponse('edit not yet implemented')
    else:
        form = UserForm(dbs=db_list, groups=group_list)

    c = {'form':form,}
    template = functions.skeleton(params['view'])
    context = RequestContext(request, {
        }, [functions.site_proc]
    )
    context.update(c)
    return HttpResponse(template.render(context))


def query(request):
    
    params = request.GET
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented')
    
    else:
        form = forms.QueryForm()
        template = functions.skeleton(params['view'])
        context = RequestContext(request, {
            'form': form}, [functions.site_proc]                          
        )
        return HttpResponse(template.render(context))
    
    
def import_(request):
    params = request.GET
    if request.method == 'POST':
        form = forms.ImportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented');
    
    elif request.method == 'GET':
        form = forms.ImportForm()
        template = functions.skeleton(params['view'])
        context = RequestContext(request, {
            'form': form}, [functions.site_proc]                          
        )
        return HttpResponse(template.render(context))


def export(request):
    params = request.GET
    if request.method == 'POST':
        form = forms.ExportForm(request.POST)
        if form.is_valid():
            return HttpResponse('feature not yet implemented');
    
    elif request.method == 'GET':
        form = forms.ExportForm()
        template = functions.skeleton(params['view'])
        context = RequestContext(request, {
            'form': form}, [functions.site_proc]                          
        )
        return HttpResponse(template.render(context))
