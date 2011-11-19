# Create your views here.
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods
from django.core import serializers

from tiote import forms, functions, views


def index(request):
    functions.set_ajax_key(request)
    request.session.set_expiry(1800)
    
    if not functions.check_login(request):
        return HttpResponseRedirect('login/')
    
    # return empty template
    c = {}
    template = functions.skeleton('start')
    context = RequestContext(request, {
        }, [functions.site_proc]
    )
    context.update(c)
    return HttpResponse(template.render(context))
        

def login(request):
    errors = []
    redi = request.META['PATH_INFO']
    redi = redi.replace('login/', '');
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            dict_cd = functions.do_login(request, form.cleaned_data)
            if dict_cd['login'] == True:
                return HttpResponseRedirect(redi)
            else:
                errors = [ dict_cd['msg'] ] 
    
    return begin(request, 'login', errors=errors)
        
        
def ajax(request):
    #check XmlHttpRequest
    if not request.is_ajax():
        # return 500 error
        return functions.http_500('not an ajax request!')
    
    if not functions.validateAjaxRequest(request):
        return functions.http_500('invalid ajax request!')
    # ajax request is okay
    
        
    if request.GET.get('check', False) and request.GET.get('check', False) == 'login':
        bool_cd = functions.check_login(request)
        if bool_cd == 'true':
            return HttpResponse('true')
        else:
            return HttpResponse('')
    
    # short GET request queries
    if request.GET.get('commonQuery'):
        return HttpResponse( functions.common_query(request, 
            request.GET.get('commonQuery')) ) 
    
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
        return views.home.route(request)
    elif request.GET.get('section', False) == 'database':
        return views.database.route(request)
    elif request.GET.get('section', False) == 'table':
        return views.table.route(request)
    else:
        return functions.http_500('request corresponses to no function!')
   


def begin(request, page, **kwargs):
    c = {} # dict to append the context
    if kwargs:
        if kwargs.has_key('errors'):
            c.update({'errors': kwargs['errors']})
    if page == 'login':
        if request.method == 'POST':
            c.update({'form': forms.LoginForm(request.POST)})
        else:
            c.update({'form': forms.LoginForm()})
    t = functions.skeleton(page)
    context = RequestContext(request, {
        }, [functions.site_proc]
    )
    context.update(c)
    h =  HttpResponse(t.render(context))
    return h

