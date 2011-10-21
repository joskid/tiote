from django import forms
from django.forms.formsets import formset_factory
from django.core import validators
from django.utils.datastructures import SortedDict

from tiote import functions

mysql_charset_choices = (('',''),('big5','big5'),('dec8','dec8'),("cp850","cp850"),("hp8","hp8"),
    ("koi8r","koi8r"),("latin1","latin1"),("latin2","latin2"),("swe7","swe7"),("ascii","ascii"),
    ("ujis","ujis"),("sjis","sjis"),("hebrew","hebrew"),("tis620","tis620"),("euckr","euckr"),
    ("koi8u","koi8u"),("gb2312","gb2312"),("greek","greek"),("cp1250","cp1250"),("gbk","gbk"),
    ("latin5","latin5"),("armscii8","armscii8"),("utf8","utf8"),("ucs2","ucs2"),("cp866","cp866"),
    ("keybcs2","keybcs2"),("macce","macce"),("macroman","macroman"),("cp852","cp852"),("latin7","latin7"),
    ("cp1251","cp1251"),("cp1256","cp1256"),("cp1257","cp1257"),("binary","binary"),("geostd8","geostd8"),
    ("cp932","cp932"),("eucjpms","eucjpms")
)

mysql_type_choices = (("varchar","varchar"),("char","char"),("text","text"),("tinytext","tinytext"),
    ("mediumtext","mediumtext"),("longtext","longtext"),("tinyint","tinyint"),("smallint","smallint"),
    ("mediumint","mediumint"),("int","int"),("bigint","bigint"),("real","real"),("double","double"),
    ("float","float"),("decimal","decimal"),("numeric","numeric"),("date","date"),("time","time"),
    ("datetime","datetime"),("timestamp","timestamp"),("tinyblob","tinyblob"),("blob","blob"),
    ("mediumblob","mediumblob"),("longblob","longblob"),("binary","binary"),("varbinary","varbinary"),
    ("bit","bit"),("enum","enum"),("set","set"),
)

pgsql_encoding = [('UTF8', 'utf8'),('SQL_ASCII', 'sql_ascii'),('BIG5', 'big5'), ('EUC_CN', 'euc_cn'), ('EUC_JP', 'euc_jp'), 
    ('EUC_KR', 'euc_kr'), ('EUC_TW', 'euc_tw'), ('GB18030', 'gb18030'), ('GBK', 'gbk'),
    ('ISO_8859_5', 'iso_8859_5'), ('ISO_8859_6', 'iso_8859_6'), ('ISO_8859_7', 'iso_8859_7'),
    ('ISO_8859_8', 'iso_8859_8'), ('JOHAB', 'johab'), ('KOI8R', 'koi8r'), ('KOI8U', 'koi8u'),
    ('LATIN1', 'latin1'), ('LATIN2', 'latin2'), ('LATIN3', 'latin3'), ('LATIN4', 'latin4'),
    ('LATIN5', 'latin5'), ('LATIN6', 'latin6'), ('LATIN7', 'latin7'), ('LATIN8', 'latin8'),
    ('LATIN9', 'latin9'), ('LATIN10', 'latin10'), ('MULE_INTERNAL', 'mule_internal'), 
    ('WIN866', 'win866'), ('WIN874', 'win874'), ('WIN1250', 'win1250'), ('WIN1251', 'win1251'), 
    ('WIN1252', 'win1252'), ('WIN1253', 'win1253'), ('WIN1254', 'win1254'), 
    ('WIN1255', 'win1255'), ('WIN1256', 'win1256'), ('WIN1257', 'win1257'), ('WIN1258', 'win1258')
]

mysql_key_choices = (('',''),('primary','primary'),('unique','unique'),('index','index'),)
mysql_other_choices = (('unsigned','Unsigned'),('binary','Binary'),('not null','Not NUll'), 
    ('auto increment','Auto Increment'),
)


user_privilege_choices = (
    ('SELECT', 'select'), ('INSERT', 'insert'), ('UPDATE', 'update'), ('DELETE', 'delete'), ('CREATE', 'create'), 
    ('DROP', 'drop'), ('ALTER', 'alter'), ('INDEX', 'index'), ('CREATE TEMPORARY TABLES', 'temp tables')
)

admin_privilege_choices = (
    ('FILE', 'file'), ('PROCESS', 'process'), ('RELOAD', 'reload'), ('SHUTDOWN', 'shutdown'), ('SUPER', 'super')
)

pgsql_privileges_choices = (
    ('SUPERUSER', 'superuser'), ('CREATEDB', 'createdb'), ('CREATEROLE', 'createrole'),
    ('INHERIT', 'inherit'),('REPLICATION', 'replication'),
)


# New Database Form
class mysqlDbForm(forms.Form):
    def __init__(self, templates=None, **kwargs):
        f = SortedDict()
        f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
        f['charset'] = forms.ChoiceField(
            choices = mysql_charset_choices,
            initial = 'latin1'
        )
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)

class pgsqlDbForm(forms.BaseForm):
    
    def __init__(self, templates=None, **kwargs):
        template_list = [('',''),] + functions.make_choices(templates)
        f = SortedDict()
        f['name'] = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
        f['encoding'] = forms.ChoiceField( choices = pgsql_encoding)
        f['template'] = forms.ChoiceField( choices = template_list,
            required = False,
        )
        
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)

#New Role/User Form
class mysqlUserForm(forms.BaseForm):
    
    def __init__(self, dbs = None, groups=None, **kwargs):
        dbs = functions.make_choices(dbs)
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
            choices = dbs,
        )
        f['privileges'] = forms.ChoiceField(
            choices = (('all', 'All Privileges'),('select','Selected Privedges'),),
            widget = forms.RadioSelect(attrs={'class':'addevnt hide_2'})
        )
    
        f['user_privileges'] = forms.MultipleChoiceField(
            required = False,
            widget = forms.CheckboxSelectMultiple(attrs={'class':'privileges'}),
            choices = user_privilege_choices,
        )
        f['administrator_privileges'] = forms.MultipleChoiceField(
            required = False,
            choices = admin_privilege_choices,
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
    
    def __init__(self, dbs=None, groups=None, **kwargs):
        group_choices = functions.make_choices(groups)
        
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
        f['account_expires'] = forms.DateField(
            required = False)
        f['connection_limit'] = forms.IntegerField(
            required = False)
        f['comment'] = forms.CharField(
            widget = forms.Textarea(attrs={'cols':'', 'rows':''}),
            required = False)
        f['role_privileges'] = forms.ChoiceField(
            required = False, widget = forms.CheckboxSelectMultiple,
            choices = pgsql_privileges_choices)
        if groups is not None:
            f['group_membership'] = forms.ChoiceField(
                choices = groups, required = False,
                widget = forms.CheckboxSelectMultiple,)
        
        self.base_fields = f
        forms.BaseForm.__init__(self, **kwargs)
    
    
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
    
    
class LoginForm(forms.Form):
    
    database_choices = ( ('', 'select database driver'),('postgresql', 'PostgreSQL'), ('mysql', 'MySQL'))
    host = forms.CharField(
        initial = 'localhost', widget=forms.TextInput(attrs=({'class':'required'}))
    )
    username = forms.CharField(
        validators = [validators.MinLengthValidator(2)], widget=forms.TextInput(attrs=({'class':'required'}))
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
    
class TableForm(forms.Form):
        
    charset_choices = (('', ''),)
    postgresql_charset_choices = (('', ''),)
    mysql_initials = {'charset': 'latin1', }
    name = forms.CharField()
    
    
class TableForm_my(TableForm):

    charset = forms.ChoiceField(
        choices = mysql_charset_choices,
        initial = 'latin1',
    )

class TableForm_gre(TableForm):
    pass


class FieldForm_my(forms.Form):
    
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'odd'}))
    type = forms.ChoiceField(
        choices = mysql_type_choices,
        widget = forms.Select(attrs={'class':'even'}),
        initial = 'varchar',
    )
    size = forms.IntegerField(widget=forms.TextInput(attrs={'class':'odd'}))
    key = forms.ChoiceField(
        required = False,
        widget = forms.Select(attrs={'class':'even'}),
        choices = mysql_key_choices,
    )
    default = forms.CharField(
        required = False,
        widget=forms.TextInput(attrs={'class':'odd'})
    )
    charset = forms.ChoiceField(
        widget = forms.Select(attrs={'class':'even'}),
        choices = mysql_charset_choices,
        initial = 'latin1'
    )
    other = forms.ChoiceField(
        widget = forms.CheckboxSelectMultiple(attrs={'class':'occupy'}),
        choices = mysql_other_choices,
        required = False,
    )
    
    
def get_dialect_form(form_name, dialect):
    '''
    structure of dialect_forms:
        { 'form_name': [ postgresql version of form_name, mysql version of form_name] }
    '''
    dialect_forms = {'DbForm': [pgsqlDbForm, mysqlDbForm],
        'UserForm': [pgsqlUserForm, mysqlUserForm],
    }
    
    return dialect_forms[form_name][0] if dialect == 'postgresql' else dialect_forms[form_name][1]
    
    