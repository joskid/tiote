import hashlib, random
from django.http import HttpResponse, Http404
from django.contrib.sessions.models import Session
from django.template import loader, RequestContext, Template


# returns page templates for each view
def skeleton(which, section=None ):
    s = section+'/' if section != None else ''
    ss = s+'tt_' + which + '.html'
    return loader.get_template(s+'tt_' + which + '.html')


def check_login(request):
    return request.session.get('TT_LOGIN', '')


def set_ajax_key(request):
    if not request.session.get('ajaxKey', False):
        sessid = hashlib.md5( str(random.random()) ).hexdigest()
        d = request.META['PWD']
        request.session['ajaxKey'] = hashlib.md5(sessid + d).hexdigest()[0:10]
        
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


def table_options(opt_type, pagination=False):
    # opt_type = "users || tbls || data
    l = ['<div class="table-options">'] # unclosed tag
    ctrls = ['all', 'none']
    # selection html
    l.append('<p class="pull-left">') # unclosed tag
    l.append('<span>{0}</span>'.format("Columns:" if opt_type=='tbls' else "Select: "))
    for ctrl in ctrls:
        l.append('<a class="selecters select_{0}">select {0}</a>'.format(ctrl))
    l.append("<span>With Selected: </span>")
    # action(ctrls) html
    if opt_type == 'users' or opt_type == 'data': 
        ctrls = ['edit', 'delete']
    elif opt_type == 'tbls':
        ctrls = ['empty', 'drop']
    for ctrl in ctrls:
        l.append('<a class="doers action_{0}">{0}</a>'.format(ctrl))
    l.append("</p></div>") # closing unopen tags
    return "".join(l)

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
    db_list = db.common_query(request, 'db_list')
    
    if request.GET.get('database') or request.GET.get('table'):
        d = {'database': request.GET.get('database')}
        db_selection_form = select_input(db_list, desc={'id':'db_select'}, initial=d['database'])
        s = ''
        if conn_params['dialect'] == 'postgresql':
            d['schema'] = request.GET.get('schema')
            # append schema selection with default to public
            schema_list = db.common_query(request, 'schema_list')
            schema_selection_form = select_input(schema_list,desc={'id':'schema_select'},initial=d['schema'])
            s += "<h6 class='icon-schemas'>schema</h6>" + schema_selection_form
        
        # table selection ul
        table_list = db.rpr_query(request, 'existing_tables')
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

    else: # home section
        li_list = []
        for db_row in db_list:
            sufx = "&schema=public" if conn_params['dialect'] == 'postgresql' else ''
            a = "<a class='icon-database' href='#section=database&view=overview&database={0}{1}'>{0}</a>".format(db_row[0],sufx)
            li_list.append('<li>{0}</li>'.format(a))
        ret_string += '<h6>Databases</h6><ul>' + ''.join(li_list) + '</ul>'
#    return ret_string
    return HttpResponse(ret_string)



class HtmlTable():
    '''
    creates a html table from the given arguments
        - properties - a dict of table attributes
        - columns - an iterable containing the table heads
        - rows - and iterable containing some iterables
    '''
    def __init__(self, columns=None, rows=None, attribs={}, props=None, store={}, **kwargs):
        self.props = props
        self.tbody_chldrn = []
        # build attributes
        default_attribs = {'class':'sql zebra-striped', 'id':'sql_table'}
        self.attribs = default_attribs
        self.attribs.update(attribs)
        self.store_list = self._build_store(store)
        self.attribs_list = self._build_attribs_list(self.attribs)
        # build <thead><tr> children
        if columns is not None:
            hd_list = []
            if self.props is not None:
                if self.props.keys().count('with_checkboxes') > 0 and self.props['with_checkboxes'] == True:
                    hd_list.append("<th class='controls'></th>")
            for head in columns:
                hd_list.append('<th>'+head+'</th>')
            self.thead_chldrn = hd_list
        # build <tbody> children
        if rows is not None:
            [self.push(row) for row in rows]       

    def _build_attribs_list(self, attribs=None):
        attribs_list = []
        if attribs is not None:
            for k in attribs.keys():
                attribs_list.append(" {0}='{1}'".format(
                    str(k).lower(), str(attribs[k]) )
                )
        return attribs_list

    def _build_store(self, store):
        store_list = []
        if store != {}:
            for key in store.keys():
                store_list.append("{0}:{1};".format(
                    str(key), str(store[key])
                    ))
        return store_list

    def push(self, row, props=None):
        count = len(self.tbody_chldrn)
        row_list = ["<tr id='row_{0}'>".format(str(count))]
        if self.props is not None:
            l_props = []
            if self.props.keys().count('with_checkboxes') > 0 and self.props['with_checkboxes'] == True:
                l_props.append("<input class='checker' id='check_{0}' type='checkbox' />".format(count))
            if self.props.keys().count('go_link') > 0 and self.props['go_link'] == True:
                l_props.append(
                    '<a href="{0}={1}" class="go_link icon-go">&nbsp;</a>'.format(
                        self.props['go_link_dest'],row[0])
                )
            tida = "<td class='controls'>{0}</td>".format("".join(l_props))
            row_list.append(tida)
        for col in row:
            row_list.append("<td>{0}</td>".format(col))
        row_list.append("</tr>")
        self.tbody_chldrn.append(row_list)
    
    def to_element(self):
        el = "<table{0}{1}><thead><tr>{2}</tr></thead><tbody>{3}</tbody></table>".format(
            ''.join(self.attribs_list), # {0}
            ' data="' + ''.join(self.store_list) +'"' if bool(self.store_list) else '', #{1}
            ''.join(self.thead_chldrn),  #{2}
            ''.join([ ''.join(row) for row in self.tbody_chldrn]) #{3}
        )
        return el

    def __str__(self):
        return self.to_element()
    
# avoid cyclic imports
import db