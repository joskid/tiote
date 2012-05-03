import json

from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods
from urllib import urlencode
from django.utils.datastructures import SortedDict
from tiote import forms, utils


def overview(request):
    '''
    A collector and disperser of 'overview' views. It appends the mini-navigation(subnav) to
    the response of 'overview' views if the request is a GET request else leave it as it is.
    '''
    conn_params = utils.fns.get_conn_params(request)
    subv = request.GET.get('subv', 'tbl') # defaults to tbl
    if subv == 'tbl': h = tbl_overview(request)
    # elif
    if request.method == 'GET':
        _subnav = {'tbl': utils.fns.ABBREVS['tbl'], 'seq':utils.fns.ABBREVS['seq']}
        # fill this list as per implementation
        implemented_dict = {
            'mysql': ('tbl',),
            'postgresql': ('tbl',)
        }
        # generate href with hash ordered as tiote needs
        dest_url = SortedDict(); _d = {'sctn':'db','v':'overview'}
        for k in _d: dest_url[k] = _d[k] # init this way to maintain order
        for k in ('db', 'schm','tbl',): 
            if request.GET.get(k): dest_url[k] = request.GET.get(k)
        # generate navigation ul
        # if the number of default elements to show is just one then skip this whole process
        if len(implemented_dict[ conn_params['dialect'] ]) > 1:
            _list = []
            for k in implemented_dict[ conn_params['dialect'] ]:
                _list.append('<li{0}><a href="{1}{2}">{3}<span>|</span></a></li>'.format(
                    ' class="active"' if _subnav[k] == _subnav[subv] else '',
                    '#'+urlencode(dest_url)+'&subv=', k, _subnav[k] +'s'
                    )
                )
            if len(_list):
                subnav_str = '<div style="margin-bottom:-5px;"><ul class="subnav">{0}</ul></div>'.format(''.join(_list))
                h.content = subnav_str + h.content
    return h


def tbl_overview(request):
    '''
    'overview' view of tables.
    '''
    conn_params = utils.fns.get_conn_params(request)
    # table deletion or emptying request catching and handling
    if request.method == 'POST' and request.GET.get('upd8'):
        # format the where_stmt to a mapping of columns to values (a dict)
        l = request.POST.get('where_stmt').strip().split(';')
        conditions = utils.fns.get_conditions(l)
        q = ''
        if request.GET.get('upd8') == 'drop':
            q = 'drop_table'
        elif request.GET.get('upd8') == 'empty':
            q = 'empty_table'
        query_data = {'db':request.GET['db'],'conditions':conditions}
        if request.GET.get('schm'):
            query_data['schm'] = request.GET.get('schm')
        h = utils.db.rpr_query(conn_params, q , query_data)
        h.set_cookie('TT_UPDATE_SIDEBAR', 'ye') # update sidebar in case there have been a deletion
        return h

    get_data = utils.fns.qd(request.GET)
    if not get_data.has_key('schm'): get_data['schm'] = 'public'
    tbl_data = utils.db.rpr_query(conn_params, 'table_rpr', get_data)
    # setup urls with SortedDict to maintain structure
    dest_url = SortedDict(); d = {'sctn':'tbl','v':'browse'}
    for k in d: dest_url[k] = d[k]
    for k in ('db', 'schm',): 
        if request.GET.get(k): dest_url[k] = request.GET.get(k) 
    conn_params = utils.fns.get_conn_params(request)
    props_keys = (('table', 'key'),)
    static_addr = utils.fns.render_template(request, '{{STATIC_URL}}')
    tables_table = utils.fns.HtmlTable(static_addr=static_addr,
        props={'count':tbl_data['count'],'with_checkboxes': True,
            'go_link': True, 'go_link_type': 'href', 
            'go_link_dest': '#'+urlencode(dest_url)+'&tbl',
            'keys': props_keys
        }, **tbl_data
        )
    if not tables_table.has_body():
        return HttpResponse('<div class="undefined">[No table has been defined in this table]</div>')
    tables_table_html = tables_table.to_element()
    table_options_html = utils.fns.table_options('tbl', with_keys=True, 
        select_actions=True)
    return HttpResponse(table_options_html + tables_table_html)
    

def route(request):
    if request.GET['v'] == 'overview':
        return overview(request)
