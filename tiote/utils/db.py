import json
from django.http import HttpResponse
from django.conf import settings

from tiote import sql
import fns


def rpr_query(conn_params, query_type, get_data={}, post_data={}):
    '''
    Run queries that have to be generated on the fly. Most queries depends on get_data, 
    while some few depends on post_data

    get_data and post_data are gotten from request.GET and request.POST or form.cleaned_data
    '''
    # common queries that returns success state as a dict only
    no_return_queries = ('create_user', 'drop_user', 'create_db','create_table',
        'drop_table', 'empty_table', 'delete_row', 'create_column', 'delete_column',)
    
    if query_type in no_return_queries:
        conn_params['db'] = get_data['db'] if get_data.has_key('db') else conn_params['db']
        query_data = {}
        query_data.update(get_data, **post_data)
        q = sql.generate_query( query_type, conn_params['dialect'],query_data)
        result = sql.short_query(conn_params, q)
        return HttpResponse( json.dumps(result) )
    
    # specific queries with implementations similar to both dialects
    elif query_type == 'user_rpr':
        if conn_params['dialect'] == 'mysql':
            conn_params['db'] = 'mysql'
        r = sql.full_query(conn_params, 
            sql.stored_query(get_data['query'],conn_params['dialect']) )
        if type(r) == dict:
            r
        else:
            return fns.http_500(r)
        
    elif query_type in ('indexes', 'primary_keys', 'foreign_key_relation'):
        
        if conn_params['dialect'] == 'postgresql': conn_params['db'] = get_data['db']
        r = sql.full_query(conn_params,
            sql.generate_query(query_type, conn_params['dialect'], get_data)[0])
        return r
        
    elif query_type in ('get_single_row',):
        sub_q_data = {'tbl': get_data['tbl'],'db':get_data['db']}
        if get_data.has_key('schm'):
            sub_q_data['schm'] = get_data['schm']
        # generate where statement
        sub_q_data['where'] = ""
        for ind in range(len(post_data)):
            sub_q_data['where'] += post_data.keys()[ind].strip() + "=" 
            sub_q_data['where'] += post_data.values()[ind].strip()
            if ind != len(post_data) - 1: sub_q_data['where'] += ' AND '
        # retrieve and run queries
        conn_params['db'] = get_data['db']
        # assert False
        q = sql.generate_query(query_type, conn_params['dialect'], sub_q_data)
        r =  sql.full_query(conn_params, q[0])
        return r
        

    elif query_type in ('table_rpr', 'table_structure', 'raw_table_structure'):
        conn_params['db'] = get_data['db']
        sub_q_data = {'db': get_data['db'],}
        if get_data.has_key('tbl'):
            sub_q_data['tbl'] = get_data['tbl']
        if get_data.has_key('schm'):
            sub_q_data['schm'] = get_data['schm']
        # make query
        if conn_params['dialect'] == 'postgresql' and query_type == 'raw_table_structure':
            q = 'table_structure'
        else: q = query_type

        r = sql.full_query(conn_params,
            sql.generate_query(q, conn_params['dialect'], sub_q_data)[0] )
        # further needed processing
        if conn_params['dialect'] == 'postgresql' and query_type.count('table_structure'):
            rwz = []
            for tuple_row in r['rows']:
                row = list(tuple_row)
                _l = [ row[1] ]
                if row[1] in ('bit', 'bit varying', 'character varying', 'character') and type(row[4]) is int:
                    _l.append( '({0})'.format(row[4]) )
                elif row[1] in ('numeric', 'decimal') and type(row[5]) is int or type(row[6]) is int:
                    _l.append( '({0},{1})'.format(row[5], row[6]) )
                elif row[1] in ('interval', 'time with time zone', 'time without time zone',
                    'timestamp with time zone', 'timestamp without time zone') and type(row[7]) is int:
                    _l.append( '({0})'.format(row[7]) )
                # append the current row to rwz
                if query_type == 'table_structure': rwz.append([row[0], "".join(_l), row[2], row[3] ])
                elif query_type == 'raw_table_structure': 
                    row.append("".join(_l))
                    rwz.append(row)
            # change r['rows']
            r['rows'] = rwz
            # change r['columns']
            if query_type == 'table_structure':
                r['columns'] = [ r['columns'][0], r['columns'][1], r['columns'][2], r['columns'][3] ]
            elif query_type == 'raw_table_structure': r['columns'].append('column_type')

        return r
        
    elif query_type == 'browse_table':
        # initializations        
        sub_q_data = {'tbl': get_data['tbl'],'db':get_data['db']}
        sub_q_data['offset'] = get_data['offset'] if get_data.has_key('offset') else 0
        sub_q_data['limit'] = get_data['limit'] if get_data.has_key('limit') else getattr(settings, 'TT_MAX_ROW_COUNT', 100)
        for item in ['schm', 'sort_key', 'sort_dir']:
            if get_data.has_key(item): sub_q_data[item] = get_data[item]
        # retrieve and run queries
        conn_params['db'] = get_data['db']
        keys = rpr_query(conn_params, 'primary_keys', sub_q_data)
        count = sql.full_query(conn_params, 
            sql.generate_query('count_rows', conn_params['dialect'], sub_q_data)[0],
            )['rows']
        r = sql.full_query(conn_params,
            sql.generate_query(query_type, conn_params['dialect'], sub_q_data)[0]
            )
        # format and return data
        if type(r) == dict:
            r.update({'total_count': count[0][0], 'offset': sub_q_data['offset'],
                      'limit':sub_q_data['limit'], 'keys': keys})
            return r
        else:
            return fns.http_500(r)
        
    # queries that just asks formats and return result
    elif query_type in ('existing_tables',):
        query_data = {'db':get_data['db'],}
        if get_data.has_key('tbl'): query_data['tbl'] = get_data['tbl']
        if conn_params['dialect'] == 'postgresql':
            query_data['schm'] = get_data['schm']
            conn_params['db'] = query_data['db']
            
        q = sql.generate_query(query_type, conn_params['dialect'], query_data)
        r =  sql.full_query(conn_params,
            q[0])
        return r['rows']

        
    # queries with dissimilar implementations
    elif conn_params['dialect'] == 'postgresql':
            return fns.http_500('query ({query_type}) not implemented!'.format(query_type=query_type))
            
    elif conn_params['dialect'] == 'mysql':
        
        if query_type == 'describe_databases':
            conn_params['db'] = 'INFORMATION_SCHEMA';
            query = sql.stored_query(query_type, conn_params['dialect'])
            return sql.full_query(conn_params, query)
        
        else:
            return fns.http_500('query not yet implemented!')
    else:
        return fns.http_500('dialect not supported!')



def fn_query(conn_params, query_name, get_data={}, post_data={}):
    '''
    reduces the growth rate of the rpr_query function above
    
    it uses a mapping to know which function to call
    
    all its queries are functions to be called not sections of stored logic like rpr_query
    '''
    query_map = {
        'get_row': get_row
    }
    
    return query_map[query_name](conn_params, get_data, post_data)


def common_query(conn_params, query_name, get_data={}):
    '''
    Run queries that needs no dynamic generation. Queries here are already stored and would
    only need to be executed on the database selected

    get_data is a django QueryDict structure
    '''
    pgsql_redundant_queries = ('template_list', 'group_list', 'user_list', 'db_list', 'schema_list')
    mysql_redundant_queries = ('db_list','charset_list', 'supported_engines')
    
    if conn_params['dialect'] == 'postgresql' and query_name in pgsql_redundant_queries :
            # this kind of queries require no special attention
            if query_name == 'schema_list':
                if hasattr(settings, 'TT_SHOW_SYSTEM_CATALOGS'):
                    query_name = 'full_schema_list' if settings.TT_SHOW_SYSTEM_CATALOGS == True else "user_schema_list"
                else: query_name = "user_schema_list" # default
            
            conn_params['db'] == get_data.get('db') if get_data.get('db') else conn_params['db']
            r = sql.full_query(conn_params,
                sql.stored_query(query_name, conn_params['dialect']))
            return r['rows']
                
    elif conn_params['dialect'] == 'mysql':
        if query_name in mysql_redundant_queries :
            # this kind of queries require no special attention
            return sql.full_query(conn_params,
                sql.stored_query(query_name, conn_params['dialect']))['rows']


def get_row(conn_params, get_data={}, post_data={}):
    r = rpr_query(conn_params, 'get_single_row', get_data, post_data)
    html = ""
    if type(r) == str: return r
    for ind in range(len(r['columns'])):
        html += '<span class="column-entry">' + str(r['columns'][ind]) + '</span>'
        html += '<br /><div class="data-entry"><code>' + str(r['rows'][0][ind]) + '</code></div>'
    # replace all newlines with <br /> because html doesn't render newlines (\n) directly
    html = html.replace('\n', '<br />')
    return html


def insert_row(conn_params, get_data={}, form_data={}):
    # set execution context
    conn_params['db'] = get_data['db']
    
    # format form_data ( from a form) according to the following rules
    # * add single qoutes to the variables
    # * make lists a concatenation of lists
    cols, values = [], []
    for k in form_data:
        if k in ('csrfmiddlewaretoken', 'save_changes_to'): continue
        cols.append(k)
        if type(form_data[k]) == list:
            value = ",".join(  form_data[k]  )
            values.append( fns.quote(value) )
        else: 
            values.append(  fns.quote( unicode(form_data[k]) )  )

    # generate sql insert statement
    q = "INSERT INTO {0}{tbl} ({1}) VALUES ({2})".format(
        '{schm}.'.format(**get_data) if conn_params['dialect'] == 'postgresql' else '',
        ",".join(cols), ",".join(values), **get_data
        )
    
    # run query and return results
    ret = sql.short_query(conn_params, (q, ))
    if ret['status'] == 'success': ret['msg'] = 'Insertion succeeded'
    # format status messages used in flow control (javascript side)
    # replaces with space and new lines with the HTML equivalents
    ret['msg'] = '<div class="alert-message block-message {0} span8 data-entry"><code>\
{1}</code></div>'.format(
        'success' if ret['status'] == 'success' else 'error',
        ret['msg'].replace('  ', '&nbsp;&nbsp;&nbsp;').replace('\n', '<br />')
    )
    return ret


def update_row(conn_params, indexed_cols={}, get_data={}, form_data={}):
    # set execution context
    conn_params['db'] = get_data['db']
    # format form_data ( from a form) according to the following rules
    # * add single qoutes to the variables
    # * make lists a concatenation of lists
    cols, values = [], []
    for k in form_data:
        if k in ('csrfmiddlewaretoken', 'save_changes_to'): continue
        cols.append(k)
        if type(form_data[k]) == list:
            value = ",".join(  form_data[k]  )
            values.append( fns.quote(value) )
        else: 
            values.append(  fns.quote( unicode(form_data[k]) )  )

    # generate SET sub statment
    _l_set = []
    for i in range(len(cols)):
        short_stmt = "=".join([cols[i], values[i]])
        _l_set.append(short_stmt)
    # generate WHERE sub statement
    _l_where = []
    for key in indexed_cols:
        short_stmt = "=".join([ key, fns.quote(  unicode(form_data[key])  ) ])
        _l_where.append(short_stmt)

    # generate full query
    q = "UPDATE {0}{tbl} SET {set_stmts} WHERE {where_stmts}".format(
        '{schm}.'.format(**get_data) if conn_params['dialect'] == 'postgresql' else '',
        set_stmts = ", ".join(_l_set), where_stmts = "AND ".join(_l_where), **get_data 
    )
    # run query and return results
    ret = sql.short_query(conn_params, (q, ))
    if ret['status'] == 'success': ret['msg'] = 'Row update succeeded'
    # format status messages used in flow control (javascript side)
    # replaces with space and new lines with the HTML equivalents
    ret['msg'] = '<div class="alert-message block-message {0} span12 data-entry"><code>\
{1}</code></div>'.format(
        'success' if ret['status'] == 'success' else 'error',
        ret['msg'].replace('  ', '&nbsp;&nbsp;&nbsp;').replace('\n', '<br />')
    )
    return ret


def do_login(request, cleaned_data):
    host = cleaned_data['host']
    username = cleaned_data['username']
    password = cleaned_data['password']
    database_driver = cleaned_data['database_driver']
    dict_post = {'username':username,'password':password,'database_driver':database_driver, 'host':host}
    if 'connection_database' in cleaned_data:
        dict_post['connection_database'] = cleaned_data['connection_database']
    dict_cd = sql.model_login(dict_post)
    if not dict_cd['login']:
        #authentication failed
        return dict_cd
    
    else:
        # authentication succeeded
        request.session['TT_LOGIN'] = 'true'
        request.session['TT_USERNAME'] = username
        request.session['TT_PASSWORD'] = password
        request.session['TT_DIALECT'] = database_driver
        request.session['TT_HOST'] = host
        if 'connection_database' in dict_post:
            request.session['TT_DATABASE'] = dict_post['connection_database']
        return dict_cd
    

def get_home_variables(request):
    p = fns.get_conn_params(request)
    variables = {'user': p['username'], 'host': p['host']}
    variables['dialect'] = 'PostgreSQL' if p['dialect'] == 'postgresql' else 'MySQL'
    result = sql.full_query( p, sql.stored_query('variables', p['dialect']))
    if p['dialect'] == 'postgresql':
        variables['version'] = result['rows'][0]
        return variables
    elif p['dialect'] == 'mysql':
        if type(result) == dict:
            ll = result['rows']
            d = {}
            for i in range( len(ll) ):
                  d[ll[i][0]] = ll[i][1]  
            variables.update(d)
            return variables
        else:
            return fns.http_500(result)
