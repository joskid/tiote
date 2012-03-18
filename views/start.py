# Create your views here.
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods
from django.core import serializers

from tiote import forms, utils, views


def index(request):
    utils.fns.set_ajax_key(request)
    request.session.set_expiry(1800)
    
    if not utils.fns.check_login(request):
        return HttpResponseRedirect('login/')
    
    # return empty template
    c = {}
    template = utils.fns.skeleton('start')
    context = RequestContext(request, {
        }, [utils.fns.site_proc]
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
            dict_cd = utils.db.do_login(request, form.cleaned_data)
            if dict_cd['login'] == True:
                return HttpResponseRedirect(redi)
            else:
                errors = [ dict_cd['msg'] ] 
    
    return begin(request, 'login', errors=errors)
        
        
def ajax(request):
    #check XmlHttpRequest
    if not request.is_ajax():
        # return 500 error
        return utils.fns.http_500('not an ajax request!')
    
    if not utils.fns.validateAjaxRequest(request):
        # might change this to send back the login page
        return utils.fns.http_500('invalid ajax request!')
    # ajax request is okay
    
        
    if request.GET.get('check', False) and request.GET.get('check', False) == 'login':
        bool_cd = utils.fns.check_login(request)
        if bool_cd == 'true':
            return HttpResponse('true')
        else:
            return HttpResponse('')
    
    # short GET request queries
    if request.GET.get('commonQuery'):
        return HttpResponse( utils.sql.common_query(request, 
            request.GET.get('commonQuery')) ) 
    
    # medium GET request queries
    if request.GET.get('q'):
        q = request.GET.get('q')
        if q == 'sidebar':
            return utils.fns.generate_sidebar(request)
        elif request.GET.get('type') == 'repr':
            return HttpResponse( utils.db.rpr_query(request, q) )
        elif request.GET.get('type') == 'full':
            return HttpResponse( utils.db.full_query(request, q) )
        else:
            return utils.fns.http_500('feature not yet implemented!')
        
        
    if not request.GET.get('view', False) and not request.GET.get('section', False):
        return utils.fns.http_500('not a complete ajax request!')
    
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
        return utils.fns.http_500('request corresponses to no function!')
   


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
    t = utils.fns.skeleton(page)
    context = RequestContext(request, {
        }, [utils.fns.site_proc]
    )
    context.update(c)
    h =  HttpResponse(t.render(context))
    return h

