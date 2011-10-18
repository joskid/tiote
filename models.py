
# sqlaclehemy modules
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exceptions import OperationalError, ProgrammingError, DatabaseError
from sqlalchemy.sql import select



def generate_query(query_type, dialect='postgresql', query_data=None):
    if dialect == 'postgresql': #postgresql-only statements
        pass
    
    elif dialect == 'mysql': # mysql-only statements

        if query_type == 'create_user':
            # create user statement
            querys = []
            q1 = "CREATE USER '{username}'@'{host}'".format(**query_data)
            if query_data['password']:
                q1 += " IDENTIFIED BY '{password}'".format(**query_data)
            
            querys.append(q1)
            # grant privileges
            q2 = "GRANT"
            if query_data['privileges'] == 'all':
                q2 += " ALL"
            elif query_data['privileges'] == 'select':
                priv_groups = ['user_privileges','administrator_privileges']
                for priv_group in priv_groups:
                    for priv_in in range( len(query_data[priv_group])):
                        if priv_in == len(query_data[priv_group]) - 1:
                            q2 += ' ' + query_data[priv_group][priv_in]
                        else:
                            q2 += ' ' + query_data[priv_group][priv_in] + ','
                            
            if query_data['select_databases'] and len(query_data['select_databases']) > 1:
                for db in query_data['select_databases']: #mutliple grant objects
                    q3 = q2 + ' ON {database}.*'.format(database = db)
                    # user specification
                    q3 += " TO '{username}'@'{host}'".format(**query_data)
                    # grant option
                    if query_data['options']:
                        q3 += " WITH {options[0]}".format(**query_data)
                    # append generated query to querys
                    querys.append(q3)
            else:
                # database access
                if query_data['access'] == 'all':
                    q4 = q2 + ' ON *.*'
                elif query_data['access'] == 'select':
                    q4 = q2 + ' ON {select_databases[0]}.*'.format(**query_data)
                    
                # user specification
                q4 += " TO '{username}'@'{host}'".format(**query_data)
                # grant option
                if query_data['options']:
                    q4 += " WITH {options[0]}".format(**query_data)
                querys.append(q4)
            return tuple( querys )
        
        elif query_type == 'drop_user':
            querys = []
            for where in query_data:
                q = "DROP USER '{user}'@'{host}'".format(**where)
                querys.append(q)
            return tuple(querys)
        
        elif query_type == 'rename_user':
            pass
        
        else:
            return None



def full_query(conn_params, query):
    '''
    executes and returns a query result
    '''
    link = URL(conn_params['dialect'],username=conn_params['username'], password=conn_params['password'],
        database=conn_params['database'])
    eng = create_engine(link)
    conn = ''
    try:
        conn = eng.connect()
        rr =  conn.execute(query)
        conn.close()
        return {'columns': rr.keys(),'count': rr.rowcount, 'rows':rr.fetchall()}
    except Exception as e:
        return str(e)


def short_query(conn_params, querys):
    """
    executes and returns the success state of the query
    """
    eng = create_engine( get_conn_link(conn_params) )
    try:
        conn = eng.connect()
        for query in querys:
            rr = conn.execute(query)
        return {'status':'successfull', 'msg':''}
    except Exception as e:
        return {'status':'failed', 'msg': str(e) }
    
    
def stored_query(query, dialect):
    if dialect == 'postgresql':
        pass
    elif dialect == 'mysql':
        if query == 'describe_databases':
            return "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_ROWS FROM tables"
        if query == 'user_list':
            return "SELECT user.`Host`, user.`User` FROM user"
        elif query == 'variables':
            return '''SHOW SESSION VARIABLES WHERE `Variable_name`='version_compile_machine' 
            OR `Variable_name`='version_compile_os' OR `variable_name`='version'
            '''
    
    
def model_login(conn_params):
    link = URL(conn_params['database_driver'], username = conn_params['username'], password= conn_params['password'])
    if conn_params['database_driver'] == 'postgresql':
        link.database = 'postgres'
    
    engine = create_engine(link)
    conn = ''
    dict_ret = {}
    try:
        conn = engine.connect()
    except OperationalError as e:
        dict_ret =  {'login': False, 'msg': str(e)}
    else:
        # todo 'msg'
        dict_ret =  {'login': True, 'msg': ''}
        conn.close()
    return dict_ret

        
    
def get_databases(conn_params):
    eng = create_engine( get_conn_link(conn_params) )
    link = eng.url
    conn = ''
    if link.drivername == 'postgresql':
        conn = create_engine(link).connect()
        query = "SELECT datname FROM pg_database WHERE datistemplate = 'f';"
    elif link.drivername == 'mysql':
        link.database = 'INFORMATION_SCHEMA'
        conn = create_engine(link).connect()
        query = "SELECT SCHEMA_NAME FROM SCHEMATA"
    
    return conn.execute(query)



def get_conn_link(conn_params):
    return '{dialect}://{username}:{password}@{host}/{database}'.format(**conn_params)

def get_tables():
    pass



def get_columns():
    pass



