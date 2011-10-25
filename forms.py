from django import forms
from django.forms.formsets import formset_factory
from django.core import validators
from django.utils.datastructures import SortedDict

from tiote import functions


mysql_types = ['varchar', 'char', 'text', 'tinytext', 'mediumtext', 'longtext', 'tinyint',
    'smallint', 'mediumint', 'int', 'bigint', 'real', 'double', 'float', 'decimal', 'numeric',
    'date', 'time', 'datetime', 'timestamp', 'tinyblob', 'blob', 'mediumblob', 'longblob', 'binary',
    'varbinary', 'bit', 'enum', 'set']

pgsql_encoding = ['UTF8', 'SQL_ASCII', 'BIG5', 'EUC_CN', 'EUC_JP', 'EUC_KR', 'EUC_TW',
    'GB18030', 'GBK', 'ISO_8859_5', 'ISO_8859_6', 'ISO_8859_7', 'ISO_8859_8', 'JOHAB',
    'KOI8R', 'KOI8U', 'LATIN1', 'LATIN2', 'LATIN3', 'LATIN4', 'LATIN5', 'LATIN6', 'LATIN7',
    'LATIN8', 'LATIN9', 'LATIN10', 'MULE_INTERNAL', 'WIN866', 'WIN874', 'WIN1250', 'WIN1251',
    'WIN1252', 'WIN1253', 'WIN1254', 'WIN1255', 'WIN1256', 'WIN1257', 'WIN1258'
]

mysql_key_choices = ('primary','unique','index')

mysql_other_choices = ('unsigned','binary','not null','auto increment' )

user_privilege_choices = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
    'ALTER', 'INDEX', 'CREATE TEMPORARY TABLES']
admin_privilege_choices = ('FILE','PROCESS','RELOAD', 'SHUTDOWN','SUPER')

pgsql_privileges_choices = ('INHERIT','CREATEDB','CREATEROLE','REPLICATION','SUPERUSER')


# New Database Form
class mysqlDbForm(forms.Form):
    def __init__(self, templates=None, users=None, charsets=None, **kwargs):
        f = SortedDict()
        f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
        f['charset'] = forms.ChoiceField(
            choices = functions.make_choices(charsets),
            initial = 'latin1'
        )
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)

class pgsqlDbForm(forms.BaseForm):
    
    def __init__(self, templates=None, users=None, charsets=None, **kwargs):
        f = SortedDict()
        
        f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
        f['encoding'] = forms.ChoiceField(
            choices = functions.make_choices(pgsql_encoding)
            )
        f['template'] = forms.ChoiceField(
            choices = functions.make_choices(templates),
            required = False,
        )
        f['owner'] = forms.ChoiceField( choices = functions.make_choices(users) ,
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
            choices = functions.make_choices(dbs, True),
        )
        f['privileges'] = forms.ChoiceField(
            choices = (('all', 'All Privileges'),('select','Selected Privedges'),),
            widget = forms.RadioSelect(attrs={'class':'addevnt hide_2'})
        )
    
        f['user_privileges'] = forms.MultipleChoiceField(
            required = False,
            widget = forms.CheckboxSelectMultiple(attrs={'class':'privileges'}),
            choices = functions.make_choices(user_privilege_choices, True),
        )
        f['administrator_privileges'] = forms.MultipleChoiceField(
            required = False,
            choices = functions.make_choices(admin_privilege_choices, True) ,
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
            required = False)
        f['connection_limit'] = forms.IntegerField(
            required = False)
#        f['comment'] = forms.CharField(
#            widget = forms.Textarea(attrs={'cols':'', 'rows':''}),
#            required = False)
        f['role_privileges'] = forms.MultipleChoiceField(
            required = False, widget = forms.CheckboxSelectMultiple,
            choices = functions.make_choices(pgsql_privileges_choices, True) 
        )
        if groups is not None:
            f['group_membership'] = forms.MultipleChoiceField(
                choices = functions.make_choices(groups, True), required = False,
                widget = forms.CheckboxSelectMultiple,)
        
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)


# table and columns creation form
class pgsqlTableForm(forms.BaseForm):
    def __init__(self, engines=None, charsets=None, edit=False, sub_form_count=1, **kwargs):
        pass
    
class mysqlTableForm(forms.BaseForm):
    
    def __init__(self, engines=None, charsets=None, edit=False, sub_form_count=1, **kwargs):
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
                choices = functions.make_choices(charsets),
                initial='latin1'
            )
            f['engine'] = forms.ChoiceField(
                required = False, 
                choices = functions.make_choices( engine_list ),
                initial = default_engine
            )
        # variable amount of sub_form_count
        # field label's are directly tied to the corresponding template
        for i in range( sub_form_count ):
            f['name'+'_'+str(i)] = forms.CharField(
                widget=forms.TextInput(attrs={'class':'required'}),
                label = 'name')
            f['type'+'_'+str(i)] = forms.ChoiceField(
                choices = functions.make_choices(mysql_types),
                widget = forms.Select(attrs={'class':'required needs-values select_requires:values_'
                    +str(i)+':set|enum select_requires:size_'+str(i)+':varchar'}),
                initial = 'varchar',
                label = 'type',
            )
            f['values'+'_'+str(i)] = forms.CharField(
                label = 'values', required = False, 
                help_text="Enter in the format: ('yes','false')",
            )
            f['size'+'_'+str(i)] = forms.IntegerField(widget=forms.TextInput,
                label = 'size', required=False, )
            f['key'+'_'+str(i)] = forms.ChoiceField(
                required = False,
                widget = forms.Select(attrs={'class':'even'}),
                choices = functions.make_choices(mysql_key_choices),
                label = 'key',
            )
            f['default'+'_'+str(i)] = forms.CharField(
                required = False,
                label = 'default',
                widget=forms.TextInput
            )
            f['charset'+'_'+str(i)] = forms.ChoiceField(
                choices = functions.make_choices(charsets), 
                initial='latin1',
                label = 'charset',
                widget=forms.Select(attrs={'class':'required'})
            )
            f['other'+'_'+str(i)] = forms.MultipleChoiceField(
                choices = functions.make_choices(mysql_other_choices, True),
                widget = forms.CheckboxSelectMultiple(attrs={'class':'occupy'}),
                required = False,
                label = 'other',
            )
        # complete form creation process
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)
   
 
class LoginForm(forms.Form):
    
    database_choices = ( ('', 'select database driver'),('postgresql', 'PostgreSQL'), ('mysql', 'MySQL'))
    host = forms.CharField(
        initial = 'localhost', widget=forms.TextInput(attrs=({'class':'required'}))
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs=({'class':'required'}))
    )
    password = forms.CharField(
        widget = forms.PasswordInput,
        required = False,
    )
    database_driver = forms.ChoiceField(
        choices = database_choices,
        validators = []
    )
    connection_database = forms.CharField(
        required=False, )
    
    
class ExportForm(forms.Form):
    format_choices = (
        ('SQL', 'sql'),('CSV', 'csv')
    )
    export_choices = (
        ('structure', 'structure'),('data', 'data')
    )
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
    sql = forms.CharField(
        help_text = 'Enter valid sql query and click query to execute',
        widget = forms.Textarea(attrs={'cols':'', 'rows':''}),
        label = '',
    )
    
    
class ImportForm(forms.Form):
    file = forms.FileField(
        help_text = 'Upload a sql file',
        
    )
    
    
def get_dialect_form(form_name, dialect):
    '''
    structure of dialect_forms:
        { 'form_name': [ postgresql version of form_name, mysql version of form_name] }
    '''
    dialect_forms = {'DbForm': [pgsqlDbForm, mysqlDbForm],
        'UserForm': [pgsqlUserForm, mysqlUserForm],
        'TableForm': [pgsqlTableForm, mysqlTableForm],
    }
    
    return dialect_forms[form_name][0] if dialect == 'postgresql' else dialect_forms[form_name][1]
    
    