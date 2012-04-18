import json

from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, utils


def overview(request):
    conn_params = utils.fns.get_conn_params(request)
    # table deletion or emptying request catching and handling
    if request.method == 'POST' and request.GET.get('upd8'):
        l = request.POST.get('where_stmt').strip().split(';');
        conditions = utils.fns.get_conditions(l)
        q = ''
        if request.GET.get('upd8') == 'drop':
            q = 'drop_table'
        elif request.GET.get('upd8') == 'empty':
            q = 'empty_table'
        query_data = {'db':request.GET['db'],'conditions':conditions}
        if request.GET.get('schm'):
            query_data['schm'] = request.GET.get('schm')
        return utils.db.rpr_query(conn_params, q , query_data)

    tbl_data = utils.db.rpr_query(conn_params, 'table_rpr', utils.fns.qd(request.GET))
    # setup urls with SortedDict to maintain structure
    from urllib import urlencode
    from django.utils.datastructures import SortedDict
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
