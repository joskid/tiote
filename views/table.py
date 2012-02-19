import json

from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, utils


def browse(request):
    # row(s) deletion request handling
    if request.method == 'POST' and request.GET.get('update') == 'delete':
        # might be needed for future corrections
#        l = request.POST.get('whereToEdit').strip().split(';');
#        conditions = utils.fns.get_conditions(l)
        conditions = [utils.fns.construct_cond(item[0], item[1]) 
            for item in utils.fns.dict_conds(request.POST.get('whereToEdit')) ]
        query_data = {'database': request.GET.get('database'),'table': request.GET.get('table'),
             'conditions': conditions}
        if request.GET.get('schema'):
            query_data['schema'] = request.GET.get('schema')
        return utils.db.rpr_query(request, 'delete_row', query_data)
    # row(s) edit/updating request handling
    elif request.method == 'POST' and request.GET.get('update') == 'edit':
        return utils.fns.http_500('feature not yet implemented!')
    
    tbl_data = utils.db.rpr_query(request, 'browse_table')
    # assert False
    browse_table_html = utils.fns.HtmlTable(
        props={'count':tbl_data['count'], 'keys': tbl_data['keys']['rows'],
            'with_checkboxes': True,
        }, 
        store = {'total_count':tbl_data['total_count'], 'offset': tbl_data['offset'],
            'limit': tbl_data['limit']
        }, **tbl_data
    ).to_element()
    table_options_html = utils.fns.table_options('data', pagination=True,
        with_keys=bool(tbl_data['keys']['rows']))

    return HttpResponse(table_options_html + browse_table_html)


def structure(request):

    # column deletion
    if request.method == 'POST' and request.GET.get('update'):
        l = request.POST.get('whereToEdit').strip().split(';');
        conditions = utils.fns.get_conditions(l)
        q = ''
        if request.GET.get('update') == 'edit':
            q = 'drop_table'
            return HttpResponse('update not yet implemented!')
        elif request.GET.get('update') == 'delete':
            q = 'delete_column'
            query_data = {'database': request.GET.get('database'), 'table': request.GET.get('table'),
                          'conditions': conditions}
            
            return utils.db.rpr_query(request, q, query_data)
        
    # view data
    tbl_struct_data = utils.db.rpr_query(request, 'table_structure')
    columns_table_html = utils.fns.HtmlTable(attribs = {'id': 'tbl_columns'},
        props = {'count': tbl_struct_data['count'], 'with_checkboxes': True,},
        **tbl_struct_data
    ).to_element()
    indexes_data = utils.db.rpr_query(request, 'indexes')
    indexes_table_html = utils.fns.HtmlTable(
        props = {'count': indexes_data['count'], 'with_checkboxes': True},
        **indexes_data
    ).to_element()
    return HttpResponse(columns_table_html+indexes_table_html)


def route(request):
    if request.GET.get('view') == 'browse':
        return browse(request)
    elif request.GET.get('view') == 'structure':
        return structure(request)
    else:
        return utils.fns.http_500('malformed URL')