import json

from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, utils


def browse(request):
    conn_params = utils.fns.get_conn_params(request)
    # row(s) deletion request handling
    if request.method == 'POST' and request.GET.get('upd8') == 'delete':
        return utils.db.rpr_query(conn_params, 'delete_row', 
            utils.fns.qd(request.GET), utils.fns.qd(request.POST))
    # row(s) edit/updating request handling
    elif request.method == 'POST' and request.GET.get('upd8') == 'edit':
        return utils.fns.http_500('feature not yet implemented!')
    tbl_data = utils.db.rpr_query(conn_params, 'browse_table', utils.fns.qd(request.GET), utils.fns.qd(request.POST))
    static_addr = utils.fns.render_template(request, '{{STATIC_URL}}')
    browse_table = utils.fns.HtmlTable(
        static_addr = static_addr,
        props={'count':tbl_data['count'], 'keys': tbl_data['keys']['rows'],
            'with_checkboxes': True, 'display_row': True,
        }, 
        store = {'total_count':tbl_data['total_count'], 'offset': tbl_data['offset'],
            'limit': tbl_data['limit']
        }, **tbl_data
    )
    if not browse_table.has_body():
        return HttpResponse('<div class="undefined">[This table contains no entry]</div>')
    browse_table_html = browse_table.to_element().replace('\n', '<br />') # html doesn't display newlines(\n)
    table_options_html = utils.fns.table_options('data', 
        with_keys=bool(tbl_data['keys']['rows']), select_actions=True)
    return HttpResponse(table_options_html + browse_table_html)


def structure(request):
    conn_params = utils.fns.get_conn_params(request)
    # column deletion
    if request.method == 'POST' and request.GET.get('upd8'):
        l = request.POST.get('whereToEdit').strip().split(';');
        conditions = utils.fns.get_conditions(l)
        q = ''
        if request.GET.get('upd8') == 'edit':
            q = 'drop_table'
            return HttpResponse('update not yet implemented!')
        elif request.GET.get('upd8') == 'delete':
            q = 'delete_column'
            query_data = {'db': request.GET.get('db'), 'table': request.GET.get('table'),
                          'conditions': conditions}
            
            return utils.db.rpr_query(conn_params, q, query_data)
        
    # view data
    static_addr = utils.fns.render_template(request, '{{STATIC_URL}}')
    subv = request.GET.get('subv', 'cols')
    d = {}
    _subnav = {'cols': 'columns', 'idxs':'indexes'}
    if subv == 'cols':
        d['title'] = _subnav[subv]
        tbl_struct_data = utils.db.rpr_query(conn_params, 'table_structure', utils.fns.qd(request.GET))
        columns_table = utils.fns.HtmlTable(attribs = {'id': 'tbl_columns'},
            props = {'count': tbl_struct_data['count'], 'with_checkboxes': True,},
            static_addr = static_addr, **tbl_struct_data
        )
        d['table'] = columns_table.to_element() if columns_table.has_body() else '<div class="undefined">[Table contains no columns]</div>'
    elif subv == 'idxs':
        d['title'] = _subnav[subv]
        indexes_data = utils.db.rpr_query(conn_params, 'indexes', utils.fns.qd(request.GET))
        indexes_table = utils.fns.HtmlTable(static_addr = static_addr,
            props = {'count': indexes_data['count'], 'with_checkboxes': True},
            **indexes_data
        )
        d['table'] = indexes_table.to_element() if indexes_table.has_body() else '<div class="undefined">[Table contains no indexes]</div>'
    # generate arranged href
    from urllib import urlencode
    from django.utils.datastructures import SortedDict
    dest_url = SortedDict(); _d = {'sctn':'tbl','v':'structure'}
    for k in _d: dest_url[k] = _d[k]
    for k in ('db', 'schm','tbl',): 
        if request.GET.get(k): dest_url[k] = request.GET.get(k)
    _l = []
    # generate navigation ul
    for k in ('cols', 'idxs',):
        _l.append('<li{0}><a href="{1}{2}">{3}<span>|</span></a></li>'.format(
            ' class="active"' if _subnav[k] == d['title'] else '',
            '#'+urlencode(dest_url)+'&subv=', k, _subnav[k])
        )
    ret_str = '<div style="margin-bottom:-5px;"><ul class="subnav">{0}</ul></div>{table}'.format(
         "".join(_l),**d)
    return HttpResponse(ret_str)

def insert(request):
    # make queries and inits
    conn_params = utils.fns.get_conn_params(request)
    tbl_struct_data = utils.db.rpr_query(conn_params, 'raw_table_structure', utils.fns.qd(request.GET))
    # keys = ['column','type','null','default','character_maximum_length','numeric_precision','numeric_scale']
    tbl_indexes_data = utils.db.rpr_query(conn_params, 'indexes', utils.fns.qd(request.GET))
    # new form

    if request.method == 'POST':
        form = forms.InsertForm(tbl_struct=tbl_struct_data, dialect=conn_params['dialect'],
            tbl_indexes=tbl_indexes_data['rows'], data=request.POST)
        if form.is_valid():
            ret = utils.db.insert_row(conn_params, utils.fns.qd(request.GET), 
                utils.fns.qd(request.POST))
            # add status messages
            ret['msg'] = '<div class="alert-message block-message {0} span8 data-entry"><code>\
{1}</code></div>'.format(
                'success' if ret['status'] == 'success' else 'error',
                ret['msg'].replace('  ', '&nbsp;&nbsp;&nbsp;').replace('\n', '<br />')
            )
            return HttpResponse(json.dumps(ret))
        else: # form contains error
            ret = {'status': 'fail', 
            'msg': utils.fns.render_template(request,"tt_form_errors.html",
                {'form': form}, is_file=True).replace('\n','')
            }
            return HttpResponse(unicode(ret))

    form = forms.InsertForm(tbl_struct=tbl_struct_data, dialect=conn_params['dialect'],
        tbl_indexes=tbl_indexes_data['rows'])

    return utils.fns.response_shortcut(request, extra_vars={'form':form,}, template='form')
    
def route(request):
    if request.GET.get('v') == 'browse':
        return browse(request)
    elif request.GET.get('v') == 'structure':
        return structure(request)
    elif request.GET.get('v') == 'insert':
        return insert(request)
    else:
        return utils.fns.http_500('malformed URL')
