# Create your views here.
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, RequestContext, Template
from django.views.decorators.gzip import gzip_page
from django.conf import settings

from tiote import forms, utils, views, sql

@gzip_page
def index(request):
    utils.fns.set_ajax_key(request)
    request.session.set_expiry(getattr(settings, 'TT_SESSION_EXPIRY', 1800) )
    
    # redirect based on the return of check_login()
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
        
# ajax calls router
@gzip_page
def ajax(request):
    conn_params = utils.fns.get_conn_params(request)
    # check if the session is still logged in
    if not utils.fns.check_login(request):
        h = HttpResponse('')
        h.set_cookie('TT_SESSION_TIMEOUT', 'true')
        return h

    # check if its and XmlHttpRequest
    if not request.is_ajax():
        # return 500 error
        return utils.fns.http_500('not an ajax request!')
    
    if not utils.fns.validateAjaxRequest(request):
        # might change this to send back the login page
        return utils.fns.http_500('invalid ajax request!')
    # ajax request is okay
    
    
    # short GET request queries
    if request.GET.get('commonQuery'):
        return HttpResponse( utils.sql.common_query(request, 
            request.GET.get('commonQuery')) ) 
    
    # medium GET request queries
    if request.GET.get('q'):
        q = request.GET.get('q')
        if q == 'sidebar':
            return utils.fns.generate_sidebar(request)
        elif request.GET.get('type') == 'fn':
            return HttpResponse(utils.db.fn_query(conn_params, q, utils.fns.qd(request.GET),
                utils.fns.qd(request.POST)) )
        elif request.GET.get('type') == 'repr':
            return HttpResponse( utils.db.rpr_query(conn_params, q, utils.fns.qd(request.GET),
                utils.fns.qd(request.POST)) )
        elif request.GET.get('type') == 'full':
            return HttpResponse( utils.db.full_query(conn_params, q, utils.fns.qd(request.GET), utils.fns.qd(request.POST)) )
        else:
            return utils.fns.http_500('feature not yet implemented!')
        
        
    if not request.GET.get('v', False) and not request.GET.get('sctn', False):
        return utils.fns.http_500('not a complete ajax request!')
    
    # call corresponding function as request.GET.get('view', False)
    if request.GET.get('v', False) == 'query':
        return query(request)
    if request.GET.get('sctn', False) == 'begin':
        return begin(request, utils.fns.qd(request.GET).get('v', False))
    if request.GET.get('sctn', False) == 'home':
        return views.home.route(request)
    elif request.GET.get('sctn', False) == 'db':
        return views.db.route(request)
    elif request.GET.get('sctn', False) == 'tbl':
        return views.tbl.route(request)
    else:
        return utils.fns.http_500('request corresponses to no function!')
   
@gzip_page
def login(request):
    c , errors = {}, []
    redi = request.META['PATH_INFO'].replace('login/', '')
    
    # if the user is already logged in take him back to the home page
    if utils.fns.check_login(request):
        return HttpResponseRedirect(redi + '#sctn=home&v=home')
    
    # dialects' info
    c['dialects'] = [
        {'dialect': 'PostgreSQL', 'dialect_package':'python-psycopg2'},
        {'dialect': 'MySQL', 'dialect_package':'python-mysqldb'}, 
    ]
    # determine enabled and disabled features
    choices = ""
    try:
        import psycopg2
        choices = "p"
    except ImportError:
        c['dialects'][0]['disabled'] = True
    try:
        import MySQLdb
        choices = "a" if choices == "p" else "m" # last driver
    except ImportError:
        c['dialects'][1]['disabled'] = True

    if request.method == 'POST':
        form = forms.LoginForm(choices=choices, data=request.POST)
        c['form'] = form
        if form.is_valid():
            dict_cd = utils.db.do_login(request, form.cleaned_data)
            if dict_cd['login'] == True: return HttpResponseRedirect(redi)
            else: c['errors'] = [ dict_cd['msg'] ] 

    if request.method == 'GET':
        form = forms.LoginForm(choices=choices)
        c['form'] = form
    
    t = loader.get_template('tt_login.html')
    context = RequestContext(request, {}, [utils.fns.site_proc])
    context.update(c)
    h = HttpResponse(t.render(context))
    return h


def begin(request, page, **kwargs):
    c = {} # dict to append the context
    if kwargs:
        if kwargs.has_key('errors'):
            c.update({'errors': kwargs['errors']})
    t = utils.fns.skeleton(page)
    context = RequestContext(request, {
        }, [utils.fns.site_proc]
    )
    context.update(c)
    h =  HttpResponse(t.render(context))
    return h


def query(request):
    '''
    This view is shown on all sections and adapts according to the section.

    It provides a form for running and returning SQL queries.
    '''
    conn_params = utils.fns.get_conn_params(request)
    if request.method == 'POST':
        f = forms.QueryForm(request.POST)
        if f.is_valid():
            query_string = request.POST.get('query')
            if request.GET.get('db', False): conn_params['db'] = request.GET.get('db')
            r = sql.full_query(conn_params, query_string)
            # if query encountered an error
            if type(r) == str:
                ret = '<div class="alert-message error block-message .span6">{0}</div>'.format(
                    r.replace('\n', '<br />').replace('  ', '&nbsp;&nbsp;&nbsp;')
                )
            # query was successful
            else:
                ret = '<div class="undefined" style="margin-bottom:10px;">[Query return {0}]</div>'.format(
                    str( r['count'] ) + " rows" if r['count'] > 0 else "no rows")
                results_table = utils.fns.HtmlTable(**r)
                if results_table.has_body():
                    ret += results_table.to_element()
            h = HttpResponse(ret)
            h.set_cookie('TT_UPDATE_SIDEBAR', 'ye') # the sidebar must be updated (in case any database object has been changed or deleted)
            return h

        else:
            ret = {'status': 'fail', 
            'msg': utils.fns.render_template(request,"tt_form_errors.html",
                {'form': f}, is_file=True).replace('\n','')
            }
            return HttpResponse(unicode(ret))
        
    f = forms.QueryForm() 
    return utils.fns.response_shortcut(request, 
        extra_vars={'form':f,'sub':'Run query', 'small_form': True}, template='form')
    
    