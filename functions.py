import hashlib, random, json

from django.http import HttpResponse, Http404
from django.contrib.sessions.models import Session
from django.template import loader, RequestContext, Template
from django.utils.datastructures import SortedDict

from tiote import models

ajaxKey = ''
    
def common_query(request, query_name):
    conn_params = get_conn_params(request)
    pgsql_redundant_queries = ['template_list', 'group_list', 'user_list', 'db_list']
    mysql_redundant_queries = ['db_list','charset_list', 'supported_engines']
    
    if conn_params['dialect'] == 'postgresql':
        if query_name == 'describe_databases':
            db_list = models.full_query(conn_params, 
                models.stored_query('db_list', conn_params['dialect']) )
            dict_db = SortedDict()
            for db in db_list['rows']:
                r = rpr_query(request, 'table_list', {'db':db[0]})['rows']
                d = SortedDict()
                for tup in r:
                    if tup[0] not in d:
                        d[ tup[0] ] = []
                    d[ tup[0] ].append((tup[1],))
                dict_db[ db[0] ] = d
            return json.dumps(dict_db)
        
        elif query_name in pgsql_redundant_queries :
            # this kind of queries require no special attention
            return models.full_query(conn_params,
                models.stored_query(query_name, conn_params['dialect']))['rows']
                
    elif conn_params['dialect'] == 'mysql':
        
        if query_name == 'db_names':
            db_names =  models.get_databases( get_conn_params(request) )
            return result_to_json(db_names)
        
        elif query_name == 'describe_databases':
            result = rpr_query(request, query_name)
            d = SortedDict()
            for tup in result['rows']:
                if tup[0] not in d:
                    d[ tup[0] ] = []
                d[ tup[0] ].append((tup[1],tup[2]))
            return json.dumps(d)
        
        elif query_name in mysql_redundant_queries :
            # this kind of queries require no special attention
            return models.full_query(conn_params,
                models.stored_query(query_name, conn_params['dialect']))['rows']
        
        
def rpr_query(request, query_type, query_data=None):
    conn_params = get_conn_params(request)
    # common queries that returns success state as a dict only
    no_return_queries = ['create_user', 'drop_user', 'create_db','create_table',
        'drop_table', 'empty_table', 'delete_row']
    
    if query_type in no_return_queries:
        conn_params['database'] = request.GET.get('database') if request.GET.get('database') else conn_params['database']
        q = models.generate_query( query_type, dialect=conn_params['dialect'],
                query_data=query_data)
        result = models.short_query(conn_params, q)
        return HttpResponse( json.dumps(result) )
    
    # specific queries with implementations similar to both dialects
    elif query_type == 'user_rpr':
        if conn_params['dialect'] == 'mysql':
            conn_params['database'] = 'mysql'
        r = models.full_query(conn_params, 
            models.stored_query(request.GET.get('query'),conn_params['dialect']) )
        if type(r) == dict:
            return jsonize_result(r)
        else:
            return http_500(r)
    
    elif query_type == 'table_rpr':
        conn_params['database'] = request.GET.get('database')
        sub_q_data = {'database': request.GET.get('database'),}
        if request.GET.get('schema'):
            sub_q_data['schema'] = request.GET.get('schema')
            
        r = models.full_query(conn_params,
            models.generate_query(query_type, conn_params['dialect'], sub_q_data)[0] )
        if type(r) == dict:
            return jsonize_result(r)
        else:
            return http_500(r)
        
    elif query_type == 'browse_table':
        # initializations        
        sub_q_data = {'table': request.GET.get('table'),'database':request.GET.get('database')}
        sub_q_data['offset'] = request.GET.get('offset') if request.GET.get('offset') else 0
        sub_q_data['limit'] = request.GET.get('limit') if request.GET.get('limit') else 100
        if request.GET.get('schema'):
            sub_q_data['schema'] = request.GET.get('schema')
        # retrieve and run queries
        conn_params['database'] = request.GET.get('database')
        q = models.generate_query('table_keys', conn_params['dialect'], sub_q_data)[0]
        keys = models.full_query(conn_params,
            q )
        count = models.full_query(conn_params, 
            models.generate_query('count_rows', conn_params['dialect'], sub_q_data)[0],
            )['rows'][0][0]
        r = models.full_query(conn_params,
            models.generate_query(query_type, conn_params['dialect'], sub_q_data)[0]
            )
        # other needed display data
        if type(r) == dict:
            r.update({'total_count': count, 'offset': sub_q_data['offset'],
                      'limit':sub_q_data['limit'], 'keys': keys})
            return jsonize_result(r)
        else:
            return http_500(r)
        
    # queries with dissimilar implementations
    elif conn_params['dialect'] == 'postgresql':
        
        if query_type == 'table_list':
            # change default database
            if 'db' in query_data:
                conn_params['database'] = query_data['db']
            return models.full_query(conn_params,
                models.stored_query(query_type, conn_params['dialect']))
        
        elif query_type == 'existing_tables':
            conn_params['database'] = request.GET['database']
            return models.full_query(conn_params,
                models.stored_query(query_type, conn_params['dialect']))['rows']

        else:
            return http_500('query not implemented!')
            
            
    elif conn_params['dialect'] == 'mysql':
        
        if query_type == 'describe_databases':
            conn_params['database'] = 'INFORMATION_SCHEMA';
            query = models.stored_query(query_type, conn_params['dialect'])
            return models.full_query(conn_params, query)
        
        else:
            return http_500('feature not yet implemented!')
    else:
        return http_500('dialect not supported!')


# returns page templates for each view
def skeleton(which, section=None ):
    s = section+'/' if section != None else ''
    ss = s+'tt_' + which + '.html'
    return loader.get_template(s+'tt_' + which + '.html')


def check_login(request):
    return request.session.get('TT_LOGIN', '')
        
def do_login(request, cleaned_data):
    host = cleaned_data['host']
    username = cleaned_data['username']
    password = cleaned_data['password']
    database_driver = cleaned_data['database_driver']
    dict_post = {'username':username,'password':password,'database_driver':database_driver, 'host':host}
    if 'connection_database' in cleaned_data:
        dict_post['connection_database'] = cleaned_data['connection_database']
    dict_cd = models.model_login(dict_post)
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
    
    
def get_conn_params(request):
    data = {}
    data['host'] = request.session.get('TT_HOST')
    data['username'] = request.session.get('TT_USERNAME')
    data['password'] = request.session.get('TT_PASSWORD')
    data['dialect'] = request.session.get('TT_DIALECT')
    if request.session.get('TT_DATABASE'):
        data['database'] = request.session.get('TT_DATABASE')
    else:
        data['database'] = '' if data['dialect'] =='mysql' else 'postgres'
    return data    

    
def set_ajax_key(request):
    if not request.session.get('ajaxKey', False):
        sessid = hashlib.md5( str(random.random()) ).hexdigest()
        d = request.META['PWD']
        request.session['ajaxKey'] = hashlib.md5(sessid + d).hexdigest()
        
def validateAjaxRequest(request):
    if request.GET.get('ajaxKey', False) and request.GET.get('ajaxKey', False) == request.session.get('ajaxKey',''):
        return True
    else:
        return False
        
        
def inside_query(request, query_name):
    if query_name == 'db_names':
        db_names =  models.get_databases( get_conn_params(request) )
        return db_names.fetchall()
    
def result_to_json(result):
    l=[row for row in result]
    ll = []
    for i in range(len(l)):
        for row in l[i]:
            ll.append(str(row))
    return json.dumps(ll)

def jsonize_result(result):
    ll = result['rows']
    for row_index in range(len(ll)):
        ll[row_index] = list( ll[row_index] )
    return json.dumps(result)

def get_home_variables(request):
    p = get_conn_params(request)
    variables = {'user': p['username'], 'host': p['host']}
    variables['dialect'] = 'PostgreSQL' if p['dialect'] == 'postgresql' else 'MySQL'
    result = models.full_query( p, models.stored_query('variables', p['dialect']))
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
            return http_500(result)
    
    
def make_choices(choices, begin_empty=False):
    ret = [] if begin_empty else [('', ''),]
    for i in range( len(choices) ):
        if type(choices[i]) == str or type(choices[i])== int:
            ret.append( (choices[i], choices[i]) )
        elif type(choices[i]) == tuple or type(choices[i]) == list:
            ret.append( (choices[i][0], choices[i][0]) )
    return ret

def site_proc(request):
    return {
        'ajaxKey': request.session.get('ajaxKey',''),
    }

def http_500(msg=''):
    response = HttpResponse(msg)
    response.status_code = '500'
    return response
    
def form_errors(request, form):
    template = skeleton('form-errors')
    context = RequestContext(request, {'form':form}, 
        [site_proc]
    )
    h = HttpResponse(template.render(context))
    h.set_cookie('tt_formContainsErrors','true')
    return h
    
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

def dict_conds(st):
    '''returns a list of list containing the cond name and cond value'''
    l = [s.strip() for s in st.split(';')]
    l_d = []
    for ii in range(len(l)):
        ll = l[ii].split('=')
        l_d.append([ll[0],ll[1]])
    return l_d


def construct_cond(k, v):
    ''' fix cases where SQL WHERE expects quotes for strings and no quotes for ints and floats'''
    st = k+'='
    try:
        st += int(v)
    except Exception:
        try:
            st += float(v)
        except Exception:
            st += '\''+v+'\''
    return st

def response_shortcut(request, template = False, extra_vars=False ):
    # extra_vars are more context variables
    template = skeleton(template) if template else skeleton(request.GET['view'], request.GET['section'])
    context = RequestContext(request, {
        }, [site_proc]
    )
    if extra_vars:
        context.update(extra_vars)
    return HttpResponse(template.render(context))

