from django import forms
from django.forms.formsets import formset_factory
from django.core import validators
from django.utils.datastructures import SortedDict

from tiote import utils

mysql_types = ['varchar', 'char', 'text', 'tinytext', 'mediumtext', 'longtext', 'tinyint',
    'smallint', 'mediumint', 'int', 'bigint', 'real', 'double', 'float', 'decimal', 'numeric',
    'date', 'time', 'datetime', 'timestamp', 'tinyblob', 'blob', 'mediumblob', 'longblob', 'binary',
    'varbinary', 'bit', 'enum', 'set']

pgsql_types = ['bigint', 'bigserial', 'bit', 'bit varying', 'boolean', 'bytea', 
    'character varying', 'character', 'cidr', 'date', 'double precision', 'inet', 'integer', 
    'lseg', 'macaddr', 'money', 'real', 'smallint', 'serial', 'text', 'time', 
    'time with time zone', 'timestamp', 'timestamp with time zone', 'uuid', 'xml']

pgsql_encoding = ['UTF8', 'SQL_ASCII', 'BIG5', 'EUC_CN', 'EUC_JP', 'EUC_KR', 'EUC_TW',
    'GB18030', 'GBK', 'ISO_8859_5', 'ISO_8859_6', 'ISO_8859_7', 'ISO_8859_8', 'JOHAB',
    'KOI8R', 'KOI8U', 'LATIN1', 'LATIN2', 'LATIN3', 'LATIN4', 'LATIN5', 'LATIN6', 'LATIN7',
    'LATIN8', 'LATIN9', 'LATIN10', 'MULE_INTERNAL', 'WIN866', 'WIN874', 'WIN1250', 'WIN1251',
    'WIN1252', 'WIN1253', 'WIN1254', 'WIN1255', 'WIN1256', 'WIN1257', 'WIN1258']

mysql_key_choices = ('primary','unique','index')

pgsql_key_choices = ('unique', 'primary', 'foreign')

mysql_other_choices = ('unsigned','binary','not null','auto increment' )

user_privilege_choices = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
    'ALTER', 'INDEX', 'CREATE TEMPORARY TABLES']
admin_privilege_choices = ('FILE','PROCESS','RELOAD', 'SHUTDOWN','SUPER')

pgsql_privileges_choices = ('INHERIT','CREATEDB','CREATEROLE','REPLICATION','SUPERUSER')

format_choices = ( ('SQL', 'sql'),('CSV', 'csv') )

export_choices = ( ('structure', 'structure'),('data', 'data') )

foreign_key_action_choices = ['no action', 'restrict', 'cascade', 'set null', 'set default']


# New Database Form
class mysqlDbForm(forms.Form):
    def __init__(self, templates=None, users=None, charsets=None, **kwargs):
        f = SortedDict()
        f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
        f['charset'] = forms.ChoiceField(
            choices = utils.fns.make_choices(charsets),
            initial = 'latin1'
        )
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)


class pgsqlDbForm(forms.BaseForm):
    
    def __init__(self, templates=None, users=None, charsets=None, **kwargs):
        f = SortedDict()
        
        f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
        f['encoding'] = forms.ChoiceField(
            choices = utils.fns.make_choices(pgsql_encoding),
            initial = 'UTF8',
            )
        f['template'] = forms.ChoiceField(
            choices = utils.fns.make_choices(templates),
            required = False,
        )
        f['owner'] = forms.ChoiceField( choices = utils.fns.make_choices(users) ,
            required = False, )
        
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)

#New Role/User Form
class mysqlUserForm(forms.BaseForm):
    
    def __init__(self, dbs = None, groups=None, **kwargs):
        f = SortedDict()
            
        f['host'] = forms.CharField(
            widget=forms.TextInput(attrs={'class':'required '}),
            initial='localhost',
        )
        f['username'] = forms.CharField(
            widget=forms.TextInput(attrs={'class':'required '})
        )
        f['password'] = forms.CharField(
            widget=forms.PasswordInput(attrs={'class':''}),
            required = False
        )    
        f['access'] = forms.ChoiceField(
            choices = (('all', 'All Databases'),('select', 'Selected Databases'),),
            widget = forms.RadioSelect(attrs={'class':'addevnt hide_1'}),
            label = 'Allow access to ',
        )
    
        f['select_databases'] = forms.MultipleChoiceField(
            required = False,
            widget = forms.CheckboxSelectMultiple(attrs={'class':'retouch'}),
            choices = utils.fns.make_choices(dbs, True),
        )
        f['privileges'] = forms.ChoiceField(
            choices = (('all', 'All Privileges'),('select','Selected Privedges'),),
            widget = forms.RadioSelect(attrs={'class':'addevnt hide_2'})
        )
    
        f['user_privileges'] = forms.MultipleChoiceField(
            required = False,
            widget = forms.CheckboxSelectMultiple(attrs={'class':'privileges'}),
            choices = utils.fns.make_choices(user_privilege_choices, True),
        )
        f['administrator_privileges'] = forms.MultipleChoiceField(
            required = False,
            choices = utils.fns.make_choices(admin_privilege_choices, True) ,
            widget = forms.CheckboxSelectMultiple(attrs={'class':'privileges'}),
        )
        f['options'] = forms.MultipleChoiceField(
            choices = (('GRANT OPTION','Grant Option'),),
            widget = forms.CheckboxSelectMultiple,
            required = False,
        )
        
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)
        
    
class pgsqlUserForm(forms.BaseForm):
    
    def __init__(self, groups=None, dbs=None, **kwargs):
        f = SortedDict()
        f['role_name'] = forms.CharField(
            widget = forms.TextInput(attrs={'class':'required'})
            )
        f['can_login'] = forms.CharField(
            widget = forms.CheckboxInput
            )
        f['password'] = forms.CharField(
            widget = forms.PasswordInput,
            required = False
            )
        f['valid_until'] = forms.DateTimeField(
            widget = forms.TextInput(attrs={}),
            required = False)
        f['connection_limit'] = forms.IntegerField(
            widget=forms.TextInput(attrs={'class':'validate-integer'}),
            required = False)
#        f['comment'] = forms.CharField(
#            widget = forms.Textarea(attrs={'cols':'', 'rows':''}),
#            required = False)
        f['role_privileges'] = forms.MultipleChoiceField(
            required = False, widget = forms.CheckboxSelectMultiple,
            choices = utils.fns.make_choices(pgsql_privileges_choices, True) 
        )
        if groups:
            f['group_membership'] = forms.MultipleChoiceField(
                choices = utils.fns.make_choices(groups, True), required = False,
                widget = forms.CheckboxSelectMultiple,)
        
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)


# table and columns creation form
class pgsqlTableForm(forms.BaseForm):
    
    def __init__(self, engines=None, charsets=None, edit=False, column_count=1, column_form=False,
        existing_tables = None, existing_columns = None, **kwargs):
        f = SortedDict()
        wdg = forms.Select(attrs={}) if existing_tables else forms.Select
        
        if edit is False:
            f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
            f['of_type'] = forms.ChoiceField(
                choices = utils.fns.make_choices(existing_tables),
                required = False, widget = wdg
                )
            f['inherit'] = forms.ChoiceField(
                choices = utils.fns.make_choices(existing_tables),
                required = False, widget = wdg
                )
        # variable number of columns
        for i in range( column_count ):
            fi = str(i)
            f['name_'+fi] = forms.CharField(
                widget=forms.TextInput(attrs={'class':'required'}),
                label = 'name')
            f['type_'+fi] = forms.ChoiceField(
                label = 'type',
                choices = utils.fns.make_choices(pgsql_types),
                widget = forms.Select(attrs={'class':'required'}),
                )
            f['length_'+fi] = forms.IntegerField(
                widget=forms.TextInput(attrs={'class':'validate-integer'}),
                label = 'length', required=False, )
            f['key_'+fi] = forms.ChoiceField(
                required = False,
                widget = forms.Select(attrs={'class':'even needs:foreign-fields:foreign'
                        +' select_requires:references_'+fi+'|column_'+fi+':foreign'}),
                choices = utils.fns.make_choices(pgsql_key_choices),
                label = 'key',
            )
            f['references_'+fi] = forms.ChoiceField(
                required= False, label = 'references',
                choices = utils.fns.make_choices(existing_tables),
                widget = forms.Select()
                )
            f['column_'+fi] = forms.ChoiceField(
                required = False, label = 'column',
                )
            f['on_update_'+fi] = forms.ChoiceField(
                required= False, label = 'on update',
                choices = utils.fns.make_choices(foreign_key_action_choices, True)
            )
            f['on_delete_'+fi] = forms.ChoiceField(
                required = False, label = 'on delete',
                choices = utils.fns.make_choices(foreign_key_action_choices, True)
            )
            f['default_'+fi] = forms.CharField(
                required = False,
                label = 'default',
                widget=forms.TextInput
            )
            f['other_'+fi] = forms.MultipleChoiceField(
                label = 'other', required = False,
                widget = forms.CheckboxSelectMultiple(),
                choices = utils.fns.make_choices(['not null'], True))
        if column_form:
            f['insert_position'] = forms.ChoiceField(
                choices = utils.fns.make_choices(['at the end of the table', 'at the beginning'], True)
                    + utils.fns.make_choices(existing_columns,False,'--------','after'),
                label = 'insert this column',
                initial = 'at the end of the table',
                widget = forms.Select(attrs={'class':'required'}),
            )
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)
        
    
class mysqlTableForm(forms.BaseForm):
    
    def __init__(self, engines=None, charsets=None, edit=False, column_count=1, column_form=False,
        existing_tables = None, existing_columns = None, **kwargs):
        f = SortedDict()
        engine_list = []
        default_engine = ''
        for tup in engines:
            engine_list.append((tup[0],))
            if tup[1] == 'DEFAULT':
                default_engine = tup[0]
        if edit is False:
            f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
            f['charset'] = forms.ChoiceField(
                choices = utils.fns.make_choices(charsets),
                initial='latin1'
            )
            f['engine'] = forms.ChoiceField(
                required = False, 
                choices = utils.fns.make_choices( engine_list ),
                initial = default_engine
            )
        # variable amount of column_count
        # field label's are directly tied to the corresponding template
        for i in range( column_count ):
            sfx = '_' + str(i)
            f['name'+sfx] = forms.CharField(
                widget=forms.TextInput(attrs={'class':'required'}),
                label = 'name')
            f['type'+sfx] = forms.ChoiceField(
                choices = utils.fns.make_choices(mysql_types),
                widget = forms.Select(attrs={'class':'required needs:values:set|enum select_requires:values'
                    +sfx+':set|enum select_requires:size'+sfx+':varchar'}),
                initial = 'varchar',
                label = 'type',
            )
            f['values'+sfx] = forms.CharField(
                label = 'values', required = False, 
                help_text="Enter in the format: ('yes','false')",
            )
            f['size'+sfx] = forms.IntegerField(
                widget=forms.TextInput(attrs={'class':'validate-integer'}),
                label = 'size', required=False, )
            f['key'+sfx] = forms.ChoiceField(
                required = False,
                widget = forms.Select(attrs={'class':'even'}),
                choices = utils.fns.make_choices(mysql_key_choices),
                label = 'key',
            )
            f['default'+sfx] = forms.CharField(
                required = False,
                label = 'default',
                widget=forms.TextInput
            )
            f['charset'+sfx] = forms.ChoiceField(
                choices = utils.fns.make_choices(charsets), 
                initial='latin1',
                label = 'charset',
                widget=forms.Select(attrs={'class':'required'})
            )
            f['other'+sfx] = forms.MultipleChoiceField(
                choices = utils.fns.make_choices(mysql_other_choices, True),
                widget = forms.CheckboxSelectMultiple(attrs={'class':'occupy'}),
                required = False,
                label = 'other',
            )
        if column_form:
            f['insert_position'] = forms.ChoiceField(
                choices = utils.fns.make_choices(['at the end of the table', 'at the beginning'], True)
                    + utils.fns.make_choices(existing_columns,False,'--------','after'),
                label = 'insert this column',
                initial = 'at the end of the table',
                widget = forms.Select(attrs={'class':'required'}),
            )
        # complete form creation process
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)


class LoginForm(forms.BaseForm):
    
    def __init__(self, templates=None, choices="a", charsets=None, **kwargs):
        f = SortedDict()
        # choices = "a" || all choices
        # choices = "m" || mysql dialect
        # , 
        # choices = "p" || postgresql dialect
        database_choices = [ ('', 'select database driver'),]
        if choices == "p" or choices == "a":
            database_choices.append(('postgresql', 'PostgreSQL'))
        if choices == "m" or choices == "a":
            database_choices.append(('mysql', 'MySQL'))
        f['host'] = forms.CharField(
            initial = 'localhost', widget=forms.TextInput(attrs=({'class':'required'}))
        )
        f['username'] = forms.CharField(
            widget=forms.TextInput(attrs=({'class':'required'}))
        )
        f['password'] = forms.CharField(
            widget = forms.PasswordInput,
            required = False,
        )
        f['database_driver'] = forms.ChoiceField(
            choices = database_choices,
            widget = forms.Select(attrs={
    #            'class':'select_requires:connection_database:postgresql'
                'class':'required'
                    }
            ),
        )
        f['connection_database'] = forms.CharField(
            required=False, 
            help_text='Optional but needed if the PostgreSQL installation does not include the default `postgres` database'
        )
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)
    
    
class ExportForm(forms.Form):
    output_choices = ( ('browser', 'browser'), ('file', 'text file'))
    format = forms.ChoiceField(
        choices = format_choices,
        help_text = 'Select the output format you want',
        widget = forms.RadioSelect,
    )
    export = forms.ChoiceField(
        choices = export_choices,
        help_text = '',
        widget = forms.CheckboxSelectMultiple
    )
    output = forms.ChoiceField(
        choices = output_choices,
        help_text = 'if the number of rows expected is quite large. It is recommended you export to file',
        widget = forms.RadioSelect,
    )
    

class QueryForm(forms.Form):
    query = forms.CharField(
        help_text = 'Enter valid sql query and click query to execute',
        widget = forms.Textarea(attrs={'cols':'', 'rows':''}),
        label = '',
    )
    
    
class ImportForm(forms.BaseForm):
    def __init__(self, include_csv = False, **kwargs):
        f = SortedDict()
        f['file'] = forms.FileField(
            help_text = 'Upload a sql file',
        )
        if include_csv:
            f['format'] = forms.ChoiceField(
                choices = output_choices,
                widget = forms.RadioSelect,
            )
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)
    
    
class pgsqlSequenceForm(forms.Form):
    
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class':'required'})
    )
    incremented_by = forms.IntegerField(
        required=False, 
        widget = forms.TextInput(attrs={'class':'validate-integer'})
    )
    min_value = forms.IntegerField(
        required=False, 
        widget = forms.TextInput(attrs={'class':'validate-integer'})
    )
    max_value = forms.IntegerField(
        required=False, 
        widget = forms.TextInput(attrs={'class':'validate-integer'})
    )
    start_value = forms.IntegerField(
        required = False, 
        widget = forms.TextInput(attrs={'class':'validate-integer'})
    )
    cache_value = forms.IntegerField(
        required =False, 
        widget = forms.TextInput(attrs={'class':'validate-integer'})
    )
    can_cycle = forms.ChoiceField(
        label = 'Can cycle?', required = False,
        widget = forms.CheckboxInput()
    )
    
    
    
def get_dialect_form(form_name, dialect):
    '''
    structure of dialect_forms:
        { 'form_name': [ postgresql version of form_name, mysql version of form_name] }
    '''
    dialect_forms = {
        'DbForm': [pgsqlDbForm, mysqlDbForm],
        'UserForm': [pgsqlUserForm, mysqlUserForm],
        'TableForm': [pgsqlTableForm, mysqlTableForm],
#        'InsertForm': [pgsqlInsertForm, mysqlInsertForm]
    }
    
    return dialect_forms[form_name][0] if dialect == 'postgresql' else dialect_forms[form_name][1]


