import hashlib, random, json

from django.http import HttpResponse, Http404
from django.contrib.sessions.models import Session
from django.template import loader, RequestContext, Template
from django.utils.datastructures import SortedDict

from tiote import models

ajaxKey = ''
sessid = ''
    
def common_query(request, query_name):
    conn_params = get_conn_params(request)
    
    if conn_params['dialect'] == 'postgresql':
        if query_name == 'db_list':
            result = models.full_query(conn_params, 
                models.stored_query(query_name, conn_params['dialect'])
            )
            return result_to_json(result)
        elif query_name == 'describe_databases':
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
        
        elif query_name == 'template_list':
            return models.full_query(conn_params,
                models.stored_query(query_name, conn_params['dialect']))['rows']
                
        elif query_name == 'group_list':
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
            jsan = json.dumps(d)
            return json.dumps(d)
        
        
        
def rpr_query(request, query_type, query_data=None):
    conn_params = get_conn_params(request)
    # queries common to both dialects
    if query_type == 'create_user':
        result = models.short_query(conn_params,
            models.generate_query( query_type, dialect=conn_params['dialect'],
                query_data=query_data)
        )
        return HttpResponse( json.dumps(result) )
    # uncommon queries
    elif conn_params['dialect'] == 'postgresql':
        
        if query_type == 'describe_databases':
            return SortedDict()
        elif query_type == 'table_list':
            # change default database
            if 'db' in query_data:
                conn_params['database'] = query_data['db']
            return models.full_query(conn_params,
                models.stored_query(query_type, conn_params['dialect']))
        elif query_type == 'user_list':
            r = models.full_query(conn_params,
                models.stored_query(query_type, conn_params['dialect']))
            if type(r) == dict:
                return jsonize_result(r)
            else:
                return http_500(r)
    
    elif conn_params['dialect'] == 'mysql':
        
        if query_type == 'describe_databases':
            conn_params['database'] = 'INFORMATION_SCHEMA';
            query = models.stored_query(query_type, conn_params['dialect'])
            return models.full_query(conn_params, query)
        
        elif query_type == 'user_list':
            conn_params['database'] = 'mysql'
            q = models.stored_query(request.GET.get('query'),conn_params['dialect'])
            r = models.full_query(conn_params, q);
            if type(r) == dict:
                return jsonize_result(r)
            else:
                return http_500(r)
            
        elif query_type == 'drop_user':
            result = models.short_query(conn_params,
                models.generate_query( query_type, dialect=conn_params['dialect'],
                    query_data=query_data)
            )
            return HttpResponse(json.dumps(result) )
        else:
            return http_500('feature not yet implemented!')
    else:
        return http_500('dialect not supported!')


def full_query():
    pass

# returns page templates for each view
def skeleton(which):
    return loader.get_template('tt_' + which + '.html')


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
        # authencation succeeded
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
    
    
def make_choices(choices):
    if choices is None:
        choices = (('',''),)
    else:
        for i in range( len(choices) ):
            choices[i] = choices[i][0],choices[i][0]
    return choices


def site_proc(request):
    return {
        'ajaxKey': request.session.get('ajaxKey',''),
    }

def http_500(msg=''):
    response = HttpResponse(msg)
    response.status_code = '500'
    return response
    
    
    
