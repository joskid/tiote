# Create your views here.
from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods
from django.core import serializers

from tiote import forms, functions, views_hm

def site_proc(request):
    return {
        'ajaxKey': functions.ajaxKey,
    }


def empty(request):
    '''
    application start
    '''
    
    functions.set_ajax_key(request)
    request.session.set_expiry(1800)
    
    if request.method == 'POST':
        # this is a login request
        
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            dict_cd = functions.do_login(request, form.cleaned_data)
            if dict_cd['login'] == True:
                return begin(request, 'empty')
            else:
                errors = [ dict_cd['msg'] ] 
                return begin(request, 'login2', errors=errors)
        else:
            return begin(request, 'login2')
    
    else:
        # return empty template
        c = {}
        template = functions.skeleton('empty')
        context = RequestContext(request, {
            }, [site_proc]
        )
        context.update(c)
        return HttpResponse(template.render(context))
        

def ajax(request):
    '''
    ajax router
    '''
    #check XmlHttpRequest
    if not request.is_ajax():
        # return 500 error
        return functions.http_500('not an ajax request')
    
    if not functions.validateAjaxRequest(request):
        return functions.http_500('Invalid ajax request!')
    # ajax request is okay
    
        
    if request.GET.get('check', False) and request.GET.get('check', False) == 'login':
        bool_cd = functions.check_login(request)
        if bool_cd == 'true':
            return HttpResponse('true')
        else:
            return HttpResponse('')
    
    # short GET request queries
    if request.GET.get('commonQuery'):
        return HttpResponse( functions.commonQuery(request) ) 
    
    # medium GET request queries
    if request.GET.get('query'):
        q = request.GET.get('query')
        if request.GET.get('type') == 'representation':
            return HttpResponse( functions.rpr_query(request, q) )
        elif request.GET.get('type') == 'full':
            return HttpResponse( functions.full_query(request, q) )
        else:
            return functions.http_500('feature not yet implemented!')
        
        
    if not request.GET.get('view', False) and not request.GET.get('section', False):
        return functions.http_500('not a complete ajax request!')
    
    # call corresponding function as request.GET.get('view', False)
    
    if request.GET.get('section', False) == 'begin':
        return begin(request, request.GET.get('view', False))
    if request.GET.get('section', False) == 'home':
        return home(request)
    elif request.GET.get('section', False) == 'database':
        return database(request)
    elif request.GET.get('view', False) == 'table':
        return table(request)
    else:
        return functions.http_500('request corresponses to no function!')
   


def begin(request, page, **kwargs):
    c = {} # dict to append the context
    if kwargs:
        if kwargs.has_key('errors'):
            c.update({'errors': kwargs['errors']})
    if page == 'login' or page == 'login2':
        if request.method == 'POST':
            c.update({'form': forms.LoginForm(request.POST)})
        else:
            c.update({'form': forms.LoginForm()})
    t = functions.skeleton(page)
    context = RequestContext(request, {
        }, [site_proc]
    )
    context.update(c)
    h =  HttpResponse(t.render(context))
    if page == 'login2':
        h.set_cookie(key='dont_touch', value='true')
    return h

# section home
def home(request):
    '''
    home section router
    '''
    params = request.GET
    if params['view'] == 'users':
        return views_hm.users(request)
    elif params['view'] == 'query':
        return views_hm.query(request)
    elif params['view'] == 'export':
        return views_hm.export(request)
    elif params['view'] == 'import':
        return views_hm.import_(request)
    elif params['view'] == 'home':
        return views_hm.home(request)
        
        



def database(request):
    pass


def table(request):
    pass

