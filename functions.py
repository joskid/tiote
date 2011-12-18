import hashlib, random, json

from django.http import HttpResponse, Http404
from django.contrib.sessions.models import Session
from django.template import loader, RequestContext, Template
from django.utils.datastructures import SortedDict

from tiote import sql

ajaxKey = ''

def rpr_query(request, query_type, query_data=None):
    conn_params = get_conn_params(request)
    # common queries that returns success state as a dict only
    no_return_queries = ['create_user', 'drop_user', 'create_db','create_table',
        'drop_table', 'empty_table', 'delete_row', 'create_column', 'delete_column']
    
    if query_type in no_return_queries:
        conn_params['database'] = request.GET.get('database') if request.GET.get('database') else conn_params['database']
        q = sql.generate_query( query_type, conn_params['dialect'],query_data)
        result = sql.short_query(conn_params, q)
        return HttpResponse( json.dumps(result) )
    
    # specific queries with implementations similar to both dialects
    elif query_type == 'user_rpr':
        if conn_params['dialect'] == 'mysql':
            conn_params['database'] = 'mysql'
        r = sql.full_query(conn_params, 
            sql.stored_query(request.GET.get('query'),conn_params['dialect']) )
        if type(r) == dict:
            return jsonize_result(r)
        else:
            return http_500(r)
        
        
    elif query_type in ['table_keys', 'primary_keys']:
        if query_data is None:
            query_data = {'database':request.GET.get('database'),'table':request.GET.get('table')}
            if request.GET.get('schema'):
                query_data['schema'] = request.GET.get('schema')
        
        if conn_params['dialect'] == 'postgresql': conn_params['database'] = query_data['database']
        r = []
        for q in sql.generate_query(query_type, conn_params['dialect'], query_data):
            r.append(sql.full_query(conn_params, q) )
        # format postgresql
        
        return r[0]
        
    
    
    elif query_type in ['table_rpr', 'table_structure']:
        conn_params['database'] = request.GET.get('database')
        sub_q_data = {'database': request.GET.get('database'),}
        if request.GET.get('table'):
            sub_q_data['table'] = request.GET.get('table')
        if request.GET.get('schema'):
            sub_q_data['schema'] = request.GET.get('schema')
        # make query
        r = sql.full_query(conn_params,
            sql.generate_query(query_type, conn_params['dialect'], sub_q_data)[0] )
        # further needed processing
        if conn_params['dialect'] == 'postgresql' and query_type =='table_structure':
            rwz = []
            for tuple_row in r['rows']:
                row = list(tuple_row)
                if row[1] in ['bit', 'bit varying', 'character varying', 'character'] and type(row[4]) is int:
                    row[1] += '({0})'.format(row[4])
                elif row[1] in ['numeric', 'decimal'] and type(row[5]) is int or type(row[6]) is int:
                    row[1] += '({0},{1})'.format(row[5], row[6])
                elif row[1] in ['interval', 'time with time zone', 'time without time zone',
                    'timestamp with time zone', 'timestamp without time zone'] and type(row[7]) is int:
                    row[1] += '({0})'.format(row[7])
                # append the current row to rwz
                rwz.append([row[0], row[1], row[2], row[3] ])
            # change r['rows']
            r['rows'] = rwz
            r['columns'] = [ r['columns'][0], r['columns'][1], r['columns'][2], r['columns'][3] ]
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
        keys = rpr_query(request, 'primary_keys', sub_q_data)
        count = sql.full_query(conn_params, 
            sql.generate_query('count_rows', conn_params['dialect'], sub_q_data)[0],
            )
        r = sql.full_query(conn_params,
            sql.generate_query(query_type, conn_params['dialect'], sub_q_data)[0]
            )
        # format and return data
        if type(r) == dict:
            r.update({'total_count': count, 'offset': sub_q_data['offset'],
                      'limit':sub_q_data['limit'], 'keys': keys})
            return jsonize_result(r)
        else:
            return http_500(r)
        
    # queries that just asks formats and return result
    elif query_type in ['existing_columns', 'existing_tables', 'table_with_columns']:
        query_data = {'database':request.GET.get('database'),'table':request.GET.get('table')}
        if conn_params['dialect'] == 'postgresql':
            query_data['schema'] = request.GET.get('schema')
            conn_params['database'] = query_data['database']
            
        q = sql.generate_query(query_type, conn_params['dialect'], query_data)
        r =  sql.full_query(conn_params,
            q[0])
        return r['rows']

        
    # queries with dissimilar implementations
    elif conn_params['dialect'] == 'postgresql':
        
        if query_type == 'table_list':
            # change default database
            if 'db' in query_data:
                conn_params['database'] = query_data['db']
            return sql.full_query(conn_params,
                sql.stored_query(query_type, conn_params['dialect']))
        
        else:
            return http_500('query not implemented!')
            
            
    elif conn_params['dialect'] == 'mysql':
        
        if query_type == 'describe_databases':
            conn_params['database'] = 'INFORMATION_SCHEMA';
            query = sql.stored_query(query_type, conn_params['dialect'])
            return sql.full_query(conn_params, query)
        
        else:
            return http_500('query not yet implemented!')
    else:
        return http_500('dialect not supported!')


def common_query(request, query_name):
    conn_params = get_conn_params(request)
    pgsql_redundant_queries = ['template_list', 'group_list', 'user_list', 'db_list', 'schema_list']
    mysql_redundant_queries = ['db_list','charset_list', 'supported_engines']
    
    if conn_params['dialect'] == 'postgresql' and query_name in pgsql_redundant_queries :
            # this kind of queries require no special attention
            conn_params['database'] == request.GET.get('database') if request.GET.get('database') else conn_params['database']
            r = sql.full_query(conn_params,
                sql.stored_query(query_name, conn_params['dialect']))
            return r['rows']
                
    elif conn_params['dialect'] == 'mysql':
        
        if query_name == 'db_names':
            db_names =  sql.get_databases( get_conn_params(request) )
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
            return sql.full_query(conn_params,
                sql.stored_query(query_name, conn_params['dialect']))['rows']
        
        

def table_with_count(request,):
    pass



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
        db_names =  sql.get_databases( get_conn_params(request) )
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
            return http_500(result)
    
def make_choices(choices, begin_empty=False, begin_value='', append_label=''):
    ret = [] if begin_empty else [('',
                        begin_value if begin_value else ''),]
    for i in range( len(choices) ):
        if type(choices[i]) == str or type(choices[i])== int:
            ret.append( (choices[i], choices[i]) )
        elif type(choices[i]) == tuple or type(choices[i]) == list:
            ret.append( (choices[i][0],
                append_label+' '+choices[i][0] if append_label else choices[i][0]) )
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
    h =  HttpResponse(template.render(context))
    if template == 'form_errors':
        h.set_cookie('tt_formContainsErrors','true')
    return h


def generate_sidebar(request):

    def select_input(rows, desc=None, initial=None):
        # build select's El attributes
        attrib_str = ''
        for k in desc.keys():
            attrib_str += " " + k +"='" + desc[k] +"'"
        # build select's options
        options_str = ''
        for row in rows:
            prefx = '' 
            if initial is not None and initial == row[0]:
                prefx = " selected='selected'"
            options_str += "<option value='{0}'{1}>{0}</option>".format(
                    row[0], prefx
                )
        # final select string
        return "<select{0}>{1}</select>".format(attrib_str, options_str)

    ret_string = ''
    
    conn_params = get_conn_params(request)
    db_list = common_query(request, 'db_list')
    if request.GET.get('section') == 'home':
        li_list = []
        for db_row in db_list:
            sufx = "&schema=public" if conn_params['dialect'] == 'postgresql' else ''
            a = "<a class='icon-database' href='#section=database&view=overview&database={0}{1}'>{0}</a>".format(db_row[0],sufx)
            li_list.append('<li>{0}</li>'.format(a))
        ret_string += '<h6>Databases</h6><ul>' + ''.join(li_list) + '</ul>'
    
    elif request.GET.get('database') or request.GET.get('table'):
        d = {'database': request.GET.get('database')}
        db_selection_form = select_input(db_list, desc={'id':'db_select'}, initial=d['database'])
        s = ''
        if conn_params['dialect'] == 'postgresql':
            d['schema'] = request.GET.get('schema')
            # append schema selection with default to public
            schema_list = common_query(request, 'schema_list')
            schema_selection_form = select_input(schema_list,desc={'id':'schema_select'},initial=d['schema'])
            s += "<h6 class='icon-schemas'>schema</h6>" + schema_selection_form
        
        # table selection ul
        table_list = rpr_query(request, 'existing_tables')
        sfx_list = []
        pg_sfx = '&schema=' + d['schema'] if conn_params['dialect']=='postgresql' else ''
        for tbl_row in table_list:
            # decide selected table
            li_pfx = " class='active'" if request.GET.get('table') == tbl_row[0] else ''
            a = "<a class='icon-table' href='#section=table&view=browse&database={0}{1}&table={2}'>{2}</a>".format(
                    d['database'], pg_sfx, tbl_row[0]
                )
            sfx_list.append("<li{0}>{1}</li>".format(li_pfx, a))
            
        sfx = "<ul>{0}</ul>".format( ''.join(sfx_list) )
        ret_string += "<h6 class='icon-databases'>databases</h6>"+ db_selection_form + s + sfx

    return ret_string



class HtmlTable():
    '''
    creates a html table from the given arguments
        - properties - a dict of table attributes
        - headers - an iterable containing the table heads
        - rows - and iterable containing some iterables
    '''
    def __init__(self, headers=None, rows=None, attribs=None, props=None):
        self.props = props
        self.tbody_chldrn = []
        self.attribs = attribs
        # build attributes
        self.attribs_list = self._build_attribs_list(attribs)
        # build <thead><tr> children
        if headers is not None:
            hd_list = []
            if self.props is not None:
                if self.props.keys().count('with_checkboxes') > 0 and self.props['with_checkboxes'] == True:
                    hd_list.append("<th class='selector'></th>")
            for head in headers:
                hd_list.append('<th>'+head+'</th>')
            self.thead_chldrn = hd_list
        # build <tbody> children
        if rows is not None:
            for row in rows:
                self.push(row)
        
    def _build_attribs_list(self, attribs=None):
        attribs_list = []
        if attribs is not None:
            for k in attribs.keys():
                attribs_list.append(" {0}='{1}'".format(
                    str(k).lower(), str(attribs[k]) )
                )
        return attribs_list

    def push(self, row, props=None):
        count = len(self.tbody_chldrn)
        row_list = ["<tr id='row_{0}'>".format(str(count))]
        if self.props is not None:
            if self.props.keys().count('with_checkboxes') > 0 and self.props['with_checkboxes'] == True:
                anc_chk = "<input class='checker' id='check_{0}' type='checkbox' />".format(count)
                tida = "<td class='selector'>{0}</td>".format(anc_chk)
                row_list.append(tida)
        for col in row:
            row_list.append("<td>{0}</td>".format(col))
        row_list.append("</tr>")
        self.tbody_chldrn.append(row_list)
    
    def to_element(self):
        el = "<table{0}><thead><tr>{1}</tr></thead><tbody>{2}</tbody></table>".format(
            ''.join(self.attribs_list), ''.join(self.thead_chldrn), 
            ''.join([ ''.join(row) for row in self.tbody_chldrn])
        )
        return el
    