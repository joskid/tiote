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

class NewDbForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
    charset = forms.ChoiceField(
        choices = mysql_charset_choices,
        initial = 'latin1'
    )

class UserForm(forms.BaseForm):
    
    def __init__(self, dbs = None, **kwargs):
        for i in range( len(dbs) ):
            dbs[i] = dbs[i][0],dbs[i][0]
        
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
        widget = forms.Textarea(attrs={'class':'xxlarge'}),
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
    

