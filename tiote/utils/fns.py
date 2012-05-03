import hashlib, random
from django.http import HttpResponse, Http404
from django.contrib.sessions.models import Session
from django.template import loader, RequestContext, Template

# a list of all the abbreviations in use
ABBREVS = {
    'sctn': 'section',
    'tbl': 'table',
    'v': 'view',
    'schm': 'schema',
    'idxs': 'indexes',
    'cols': 'columns',
    'seq': 'sequence',
}

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

    
def make_choices(choices, begin_empty=False, begin_value='', append_label=''):
    '''
    Duplicate each item in choices to make a (stored_name, display_name) pair.

    Prepends the return sequence with an empty pair if begin_empty is True.

    Or could accept and optional begin_value to be the prepended pair as explained above.
    '''
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
        ll = l[i].strip().split('/i/AND/o/')
        d = {}
        for ii in range( len(ll) ):
            lll = ll[ii].strip().split('=')
            d.update( {lll[0].lower() : lll[1].lower()} )
        conditions.append(d)
    return conditions

def response_shortcut(request, template = False, extra_vars=False ):
    '''
    A view response shortcut which finds the required template by some concatenating and then
    process the return object with a RequestContext and some optional context as specified in 
    the ``extra_vars`` parameter
    '''
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
    '''
    ugly function
    returns an object instead of a list as the norms of QuerySets
    '''
    return dict((key, query_dict.get(key)) for key in query_dict)

def table_options(opt_type, with_keys=True, select_actions=False):
    '''
    Generates a textual represenation (not unicode) of div.table-options for jsified Tables.
    This html serves as a sort of toolbars (compulsory) to the operations on a jsified table.
    '''
    # opt_type = "users || tbls || data
    l = ['<div class="table-options">'] # unclosed tag
    ctrls = ['all', 'none']
    # selection html
    l.append('<p class="">') # unclosed tag
    if not with_keys:
        l.append('<span style="color:#888;">[No primary keys defined]</span>')
    else:
        l.append('<span>{0}</span>'.format("Columns:" if opt_type=='tbls' else "Select: "))
        for ctrl in ctrls:
            l.append('<a class="selector select_{0}">{1}</a>'.format(ctrl, ctrl.title()))
        if select_actions == True:
            l.append("<span>With Selected: </span>")
            # action(ctrls) html
            if opt_type == 'user' or opt_type == 'data': 
                ctrls = ['edit', 'delete']
            elif opt_type == 'tbl':
                ctrls = ['empty', 'drop']
            for ctrl in ctrls:
                l.append('<a class="doer needy_doer action_{0}">{1}</a>'.format(ctrl, ctrl.title()))
            # add a refresh link for opt_type 'data'
            if opt_type == 'data':
                l.append('<a class="doer action_refresh" style="margin-left:20px">Refresh</a>')

    l.append("</p></div>") # closing unopen tags
    return "".join(l)


def select_input(rows, desc=None, initial=None):
    '''
    Creates html select elements from the sequence 'rows', with an initial value of 
    ``initial`` if it is not None and some options description to the element if 'desc'
    is not none
    '''
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


def generate_sidebar(request):

    ret_string = '' # store the string representation to be generated by this function
    static_addr = render_template(request, '{{STATIC_URL}}') 
    conn_params = get_conn_params(request)
    db_list = db.common_query(conn_params, 'db_list', request.GET)

    # if sctn is 'home' give list of database
    # if sctn is overview give list of schema if postgresql or leave as above
    # if sctn is not 'home' or 'oveview' give a list of all the objects described by sctn
    if request.GET.get('sctn') == 'home' or \
    (conn_params['dialect'] == 'mysql' and request.GET.get('sctn') == 'db'):
        li_list = []
        for db_row in db_list:
            sufx = "&schm=public" if conn_params['dialect'] == 'postgresql' else ''
            a = "<a class='icon-database' href='#sctn=db&v=overview&db={0}{1}'>{0}</a>".format(db_row[0],sufx)
            active_li = ' class="active"' if request.GET.get('db') == db_row[0] else '' # this would mark an item for hightlighting 
                                                                                        # occurs in the 'db' section of MySQL dialect
                                                                                        # and it selects the currently displayed db
            li_list.append('<li{1}>{0}</li>'.format(a, active_li)) 
        ret_string += '<h6>Databases</h6><ul>' + ''.join(li_list) + '</ul>'

    elif request.GET.get('sctn') == 'db':
        # decide on what to do
        _dict = {'db': request.GET.get('db')}
        # get a dropdown of databases from db_list with its initial set to what is in request.GET
        db_selection_form = select_input(db_list, desc={'id':'db_select'}, initial= _dict['db'])
        schema_list = db.common_query(conn_params, 'schema_list', request.GET)
        _list = []
        for schm_row in schema_list:
            a = '<a class="icon-schema" href="#sctn=db&v=overview&db={0}&schm={1}">{1}</a>'.format(
                    _dict['db'], schm_row[0]
                )
            # decide selected schema link
            li_pfx = " class='active'" if request.GET.get('schm', 'public') == schm_row[0] else ''
            # append whole li element
            _list.append("<li{0}>{1}</li>".format(li_pfx, a))
            
        placeholder = '<h6 class="placeholder">%ss:</h6>' % ABBREVS['schm']
        sfx = "<ul>{0}</ul>".format( ''.join(_list) )

        ret_string = '<h6><a class="icon-back" href="#sctn=home&v=home">back home</a></h6>\
<h6>quick nav:</h6><div class="sidebar-item"><img src="{3}/img/databases.png" />{0}</div>{1}{2}'.format( 
            db_selection_form, placeholder, sfx, static_addr
        )

    elif request.GET.get('sctn') in ('tbl', 'seq', 'views') :
        _dict = {'db': request.GET.get('db')}
        # get a dropdown of databases from db_list with its initial set to what is in request.GET
        db_selection_form = select_input(db_list, desc={'id':'db_select'}, initial= _dict['db'])

        s = ''
        if conn_params['dialect'] == 'postgresql':
            _dict['schm'] = request.GET.get('schm')
            # append schema selection with default to public
            schema_list = db.common_query(conn_params, 'schema_list', request.GET)
            schema_selection_form = select_input(schema_list,desc={'id':'schema_select'},initial=_dict['schm'])
            # s = '<div class="sidebar-item"><img class="icon-schemas" />' + schema_selection_form + "</div>"
            s = '<div class="sidebar-item"><img src="{1}/img/schemas.png" />{0}</div>'.format(
                schema_selection_form, static_addr)
        
        # table selection ul
        table_list = db.rpr_query(conn_params, 'existing_tables', qd(request.GET))
        sfx_list = []
        pg_sfx = '&schm=' + _dict['schm'] if conn_params['dialect']=='postgresql' else ''
        for tbl_row in table_list:
            # decide selected table
            li_pfx = " class='active'" if request.GET.get('tbl') == tbl_row[0] else ''
            a = '<a class="icon-table" href="#sctn=tbl&v=browse&db={0}{1}&tbl={2}">{2}</a>'.format(
                    _dict['db'], pg_sfx, tbl_row[0]
                )
            sfx_list.append("<li{0}>{1}</li>".format(li_pfx, a))
            
        # generate the string to be returned. It has the following order
        # 1. h6 saying 'quick navigation'
        # 2. db selection select element and schm selection select element if dialect is postgresql
        # 3. a h6.placeholder element shouting 'object types:'
        # 4. a ul having li > a each saying the specific 'object type' and linking to its appropriate view
        # ret_string = '<h6>quick nav:</h6><div><a class="james pull-right" href="">overview</a></div><br />\
        bck_lnk = '<h6><a class="icon-back" href="#sctn=db&v=overview&db={0}{1}">back to overview</a>'.format(
            request.GET.get('db'),
            '&schm=%s' % request.GET.get('schm') if request.GET.get('schm') else ''
            )
        ret_string = bck_lnk + '</h6>\
<h6>quick nav:</h6><div class="sidebar-item"><img src="{4}/img/databases.png" /> {0}</div>{1}{2}{3}'.format( 
            db_selection_form, s, # 0 & 1
            '<h6 class="placeholder">%ss:</h6>' % ABBREVS[request.GET.get('sctn')], # 2
            "<ul>{0}</ul>".format( ''.join(sfx_list) ), # 3
            static_addr # 4
        )

#    return ret_string
    return HttpResponse(ret_string)



class HtmlTable():
    '''
    creates a html table from the given arguments
        - properties - a dict of table attributes
        - columns - an iterable containing the table heads
        - rows - and iterable containing some iterables

    structure of return string (html)

    <div class='jsifyTable'>
        <div class='tbl-header'><table><tbody><tr></tr></tbody></table></div>
        <div class='tbl-body'>
            <table class='sql'><tbody>
                <tr><td><div class='data-entry'><code>{{data}}</code></div></td></tr>
            </tbody></table>
        </div>
    </div>
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

# render the given template with a RequestContext(main reeason)
def render_template(request, template, context= {}, is_file=False):
    '''
    Helper function which uses ``request`` to get the RequestContext which is used 
    to provide extras context and renders the given template.
    '''
    _context = RequestContext(request, [site_proc])
    if len(context) > 0: _context.update(context)
    t = loader.get_template(template) if is_file else Template(template) 
    return t.render(_context)


def parse_indexes_query(tbl_indexes, needed_indexes=None):
    '''
    Creates a dict mapping with key as name of the column which maps to a list
    which contains all the indexes on the said key. 

    Returns a Bucket dict (like django QuerySets)

    e.g.
        {
            'id': ['PRIMARY KEY'],
            'NAME': ['UNIQUE', 'FOREIGN KEY'],
        }
    '''
    _dict = {}

    for row in tbl_indexes:
        if needed_indexes != None and row[2] not in needed_indexes: continue
        if _dict.has_key(row[0]): _dict[ row[0] ].append( row[2] )
        else: _dict[ row[0] ] = [ row[2] ]
    return _dict


def quote(_str):
    '''
    return a single quoted version of the passed in string _str
    '''
    return "'%s'" % _str
    
# cyclic import
import db