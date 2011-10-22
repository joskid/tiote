import datetime
# sqlaclehemy modules
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exceptions import OperationalError, ProgrammingError, DatabaseError
from sqlalchemy.sql import select

def stored_query(query, dialect):
    if dialect == 'postgresql':
        if query == 'variables':
            return "SHOW server_version"
        elif query == 'template_list':
            return "SELECT datname FROM pg_database WHERE datistemplate=True"
        elif query == 'group_list':
            return "SELECT rolname FROM pg_roles WHERE rolcanlogin=False"
        elif query == 'db_list':
            return "SELECT datname FROM pg_database WHERE datistemplate = 'f';"
        elif query == 'user_list':
            return "SELECT rolname, rolcanlogin, rolsuper, rolinherit, rolvaliduntil FROM pg_roles"
        elif query == 'table_list':
            return "SELECT schemaname, tablename FROM pg_tables ORDER BY schemaname DESC"
        
    elif dialect == 'mysql':
        if query == 'describe_databases':
            return "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_ROWS FROM tables"
        elif query == 'db_list':
            return "SHOW databases"
        elif query == 'user_list':
            return "SELECT user.`Host`, user.`User` FROM user"
        elif query == 'variables':
            return '''SHOW SESSION VARIABLES WHERE `Variable_name`='version_compile_machine' 
            OR `Variable_name`='version_compile_os' OR `variable_name`='version'
            '''
    

def generate_query(query_type, dialect='postgresql', query_data=None):
    if dialect == 'postgresql': #postgresql-only statements
        if query_type == 'create_user':
            # create role statement
            q0 = "CREATE ROLE {role_name}".format(**query_data)
            if query_data['can_login']:
                q0 += " LOGIN"
            if query_data['password']:
                q0 += " ENCRYPTED PASSWORD '{password}'".format(**query_data)
            if query_data['role_privileges']:
                for option in query_data['role_privileges']:
                    q0 += " " + option
            if query_data['connection_limit']:
                q0 += " CONNECTION LIMIT {connection_limit}".format(**query_data)
            if query_data['valid_until']:
                q0 += " VALID UNTIL '{valid_until}'".format(**query_data)
            if query_data['group_membership']:
                q0 += " IN ROLE"
                for grp_index in range( len(query_data['group_membership']) ):
                    if grp_index == len(query_data['group_membership']) - 1:
                        q0 += " " + query_data['group_membership'][grp_index]
                    else:
                        q0 += " " + query_data['group_membership'][grp_index] + ","
#            if query_data['comment']:
#                q1 = "COMMENT ON ROLE {role_name} IS \'{comment}\'".format(**query_data)
#                queries.append(q1)
            queries = [q0, ]
            return queries
                
    
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
    eng = create_engine(get_conn_link(conn_params))
    conn = ''
    try:
        conn = eng.connect()
        query_result =  conn.execute(query)
        d = {}
        l = []
        for row in query_result:
            row = list(row)
            for i in range(len(row)):
                if type( row[i] ) == datetime.datetime:
                    row[i] = row[i].__str__()
            l.append( tuple(row) )
        d =  {'columns': query_result.keys(),'count': query_result.rowcount, 
            'rows': l}
        conn.close()
        return d
    except Exception as e:
        conn.close()
        return str(e)


def short_query(conn_params, querys):
    """
    executes and returns the success state of the query
    """
    eng = create_engine( get_conn_link(conn_params) )
    conn = ''
    try:
        conn = eng.connect()
        for query in querys:
            query_result = conn.execute(query)
        return {'status':'successfull', }
    except Exception as e:
        conn.close()
        return {'status':'failed', 'msg': str(e) }
    
    
def model_login(conn_params):
    link = URL(conn_params['database_driver'], username = conn_params['username'],
        password= conn_params['password'], host = conn_params['host'])
    if 'connection_database' in conn_params and conn_params['database_driver'] == 'postgresql':
        link.database = conn_params['connection_database'] if conn_params['connection_database'] else 'postgres'
    if not 'connection_database' in conn_params and conn_params['database_driver'] == 'postgresql':
        link.database = 'postgres'
    l = str(link)
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
 


def get_conn_link(conn_params):
    return '{dialect}://{username}:{password}@{host}/{database}'.format(**conn_params)

def get_tables():
    pass



def get_columns():
    pass



