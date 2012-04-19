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
        try: # some environments eg. GAE doesn't have this
            d = request.META['PWD']
        except KeyError:
            d = ""
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

def response_shortcut(request, template = False, extra_vars=False ):
    # extra_vars are more context variables
    template = skeleton(template) if template else skeleton(request.GET['v'], request.GET['sctn'])
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
        data['db'] = request.session.get('TT_DATABASE')
    else:
        data['db'] = '' if data['dialect'] =='mysql' else 'postgres'
    return data    

def qd(query_dict):
    return dict((key, query_dict.get(key)) for key in query_dict)

def table_options(opt_type, with_keys=True, select_actions=False):
    # opt_type = "users || tbls || data
    l = ['<div class="table-options">'] # unclosed tag
    ctrls = ['all', 'none']
    # selection html
    l.append('<p class="pull-left">') # unclosed tag
    if not with_keys:
        l.append('<span style="color:#888;">[No primary keys defined]</span>')
    else:
        l.append('<span>{0}</span>'.format("Columns:" if opt_type=='tbls' else "Select: "))
        for ctrl in ctrls:
            l.append('<a class="selecters select_{0}">select {0}</a>'.format(ctrl))
        if select_actions == True:
            l.append("<span>With Selected: </span>")
            # action(ctrls) html
            if opt_type == 'user' or opt_type == 'data': 
                ctrls = ['edit', 'delete']
            elif opt_type == 'tbl':
                ctrls = ['empty', 'drop']
            for ctrl in ctrls:
                l.append('<a class="doers action_{0}">{0}</a>'.format(ctrl))
    l.append("</p></div>") # closing unopen tags
    return "".join(l)

def generate_sidebar(request):

    def select_input(rows, desc=None, initial=None):
        # build select's El attributes
        _l_attrib_str = []
        for k in desc.keys():
            _l_attrib_str.extend([" ", k, "='", desc[k], "'"])
        attrib_str = "".join(_l_attrib_str)
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
    
    if request.GET.get('db') or request.GET.get('tbl'):
        d = {'db': request.GET.get('db')}
        db_selection_form = select_input(db_list, desc={'id':'db_select'}, initial=d['db'])
        s = ''
        if conn_params['dialect'] == 'postgresql':
            d['schm'] = request.GET.get('schm')
            # append schema selection with default to public
            schema_list = db.common_query(request, 'schema_list')
            schema_selection_form = select_input(schema_list,desc={'id':'schema_select'},initial=d['schm'])
            s += '<h6 class="icon-schemas">schema</h6>' + schema_selection_form
        
        # table selection ul
        table_list = db.rpr_query(conn_params, 'existing_tables', qd(request.GET))
        sfx_list = []
        pg_sfx = '&schm=' + d['schm'] if conn_params['dialect']=='postgresql' else ''
        for tbl_row in table_list:
            # decide selected table
            li_pfx = " class='active'" if request.GET.get('tbl') == tbl_row[0] else ''
            a = '<a class="icon-table" href="#sctn=tbl&v=browse&db={0}{1}&tbl={2}">{2}</a>'.format(
                    d['db'], pg_sfx, tbl_row[0]
                )
            sfx_list.append("<li{0}>{1}</li>".format(li_pfx, a))
            
        sfx = "<ul>{0}</ul>".format( ''.join(sfx_list) )
        ret_string += '<h6 class="icon-databases">databases</h6>'+ db_selection_form + s + sfx

    else: # home section
        li_list = []
        for db_row in db_list:
            sufx = "&schm=public" if conn_params['dialect'] == 'postgresql' else ''
            a = "<a class='icon-database' href='#sctn=db&v=overview&db={0}{1}'>{0}</a>".format(db_row[0],sufx)
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
    def __init__(self, columns=[], rows=[], attribs={}, props={}, store={}, static_addr = "", **kwargs):
        self.props = props
        self.tbody_chldrn = []
        # build attributes
        _attribs = {'class':'sql zebra-striped', 'id':'sql_table'}
        _attribs.update(attribs)
        self.attribs_list = self._build_attribs_list(_attribs)
        self.store_list = self._build_store_list(store)
        # store the keys in the table's markup
        self.keys_list = []
        if self.props.has_key('keys'):
            self.keys_list = self._build_keys_list(self.props['keys'])
            self.keys_column = [x[0] for x in self.props['keys']]
        # build <thead><tr> children
        if columns is not None:
            self.columns = columns
            hd_list = ["<td class='controls'><div></div></td>"]
            for head in columns:
                hd_list.append('<td><div>'+head+'</div></td>')
            # empty td 
            hd_list.append('<td class="last-td"></td>')
            self.thead_chldrn = hd_list
        # build <tbody> children
        if rows is not None:
            [self.push(row, static_addr=static_addr) for row in rows]       

    def _build_attribs_list(self, attribs=None):
        attribs_list = []
        if attribs is not None:
            for k in attribs.keys():
                attribs_list.append(" {0}='{1}'".format(
                    str(k).lower(), str(attribs[k]) )
                )
        return attribs_list

    def _build_store_list(self, store):
        _l = []
        if store != {}:
            for key in store.keys():
                _l.append("{0}:{1};".format(str(key), str(store[key])  ))
        return _l

    def _build_keys_list(self, keys):
        _l = []
        if _l is not []:
            for tup in keys:
                _l.append("{0}:{1};".format(tup[0], tup[len(tup) - 1]) )
        return _l

    def has_body(self):
        return len(self.tbody_chldrn) > 0

    def push(self, row, static_addr="", props=None):
        count = len(self.tbody_chldrn)
        row_list = ["<tr id='row_{0}'>".format(str(count))]
        l_props = []
        if self.props is not None and self.props.has_key('keys') \
                and len(self.props['keys']) > 0 :
            # els a.checkers would be added for all tables with self.props['keys'] set
            l_props.append("<input class='checker' id='check_{0}' type='checkbox' />".format(count))
            # go_link adds anchors in every row 
            # go_link_type determines the characteristics of the anchor: href || onclick
            if self.props.has_key('go_link') > 0 and self.props['go_link'] == True:
                l_props.append( 
                    '<a href="{0}={1}" class="go_link">{2}</a>'.format(
                        self.props['go_link_dest'],row[0],
                        '<img src="{0}/img/goto.png" />'.format(static_addr)
                    )
                )
            if self.props.keys().count('display_row') > 0 and self.props['display_row'] == True:
                l_props.append(
                    '<a class="go_link display_row pointer"><img src="{0}/img/goto.png" /></a>'.format(static_addr)
                )
        tida = '<td class="controls"{1}><div class="data-entry">{0}</div></td>'.format(
            "".join(l_props),
            ' style="min-width:' + str(len(l_props) * 18) + 'px"' if len(l_props) else '25px"'
            )
        row_list.append(tida)

        for i in range(len(row)):
            if len(str(row[i])) > 40 and hasattr(self, 'keys_column') and not self.keys_column.count(self.columns[i]):
                if str(row[i]).count('\n') and str(row[i]).find('\n') < 40:
                    column_data = str(row[i])[0:str(row[i]).find('\n')]
                else: column_data = str(row[i])[0:40]
                column_data += '<span class="to-be-continued">...</span>'
            else:
                column_data = str(row[i])
            column_data = column_data.replace(' ', '&nbsp;') # tds with spaces in them have its width set to its min-width
            row_list.append('<td><div class="data-entry"><code>{0}</code></div></td>'.format(str(column_data)))

        # empty td
        row_list.append('<td class="last-td"></td>')
        row_list.append("</tr>")
        self.tbody_chldrn.append(row_list)
    
    def to_element(self):
        thead = '<div class="tbl-header"><table><tbody><tr>{0}</tr></tbody></table></div>'.format(
            ''.join(self.thead_chldrn)
        )

        tbody = '<div class="tbl-body"><table{0}{1}{2}><tbody>{3}</tbody></table></div>'.format(
            ''.join(self.attribs_list), # {0}
            ' data="' + ''.join(self.store_list) +'"' if bool(self.store_list) else '', #{1}
            ' keys="' + ''.join(self.keys_list) + '"' if bool(self.keys_list) else '' , #{2}
            ''.join([ ''.join(row) for row in self.tbody_chldrn])
        )
        
        return '<div class="jsifyTable">' + thead + tbody + '</div>'

    def __str__(self):
        return self.to_element()

def render_template(request, template, context= {}, is_file=False):
    _context = RequestContext(request, [site_proc])
    if len(context) > 0: _context.update(context)
    t = loader.get_template(template) if is_file else Template(template) 
    return t.render(_context)

# cyclic import
import db