from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError, ProgrammingError, \
    DatabaseError
import datetime
# sqlaclehemy modules

def stored_query(query, dialect):
    # db of stored queries
    stored_query_db = {
        'postgresql': {
            'variables':
                "SHOW server_version",
            'template_list':
                "SELECT datname FROM pg_catalog.pg_database",
            'group_list':
                "SELECT rolname FROM pg_catalog.pg_roles WHERE rolcanlogin=False",
            'db_list':
                "SELECT datname FROM pg_catalog.pg_database WHERE datistemplate = 'f' ORDER BY datname ASC;",
            'user_rpr':
                "SELECT rolname, rolcanlogin, rolsuper, rolinherit, rolvaliduntil FROM pg_catalog.pg_roles",
            'user_list':
                "SELECT rolname FROM pg_catalog.pg_roles",
            'table_list':
                "SELECT schemaname, tablename FROM pg_catalog.pg_tables ORDER BY schemaname DESC",
            'full_schema_list':
                "SELECT schema_name, schema_owner FROM information_schema.schemata \
WHERE schema_name NOT LIKE '%pg_toast%' AND schema_name NOT LIKE '%pg_temp%'",
            'user_schema_list':
                "SELECT schema_name, schema_owner FROM information_schema.schemata \
WHERE schema_name NOT LIKE '%pg_toast%' AND schema_name NOT LIKE '%pg_temp%' \
AND schema_name NOT IN ('pg_catalog', 'information_schema')"
        },

        'mysql': {
            'describe_databases': 
                "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_ROWS FROM `information_schema`.`tables`",
            'db_list':
                "SHOW databases",
            'user_rpr':
                "SELECT user.`Host`, user.`User` FROM user",
            'user_list':
                "SELECT user.`User` FROM user",
            'supported_engines':
                "SELECT engine, support FROM `information_schema`.`engines` \
                WHERE support='yes' OR support='default'",
            'charset_list':
                "SELECT CHARACTER_SET_NAME FROM INFORMATION_SCHEMA.CHARACTER_SETS",
            'variables':
                '''SHOW SESSION VARIABLES WHERE `Variable_name`='version_compile_machine' 
                OR `Variable_name`='version_compile_os' OR `variable_name`='version'
                '''     
        }
    }        
    
    # 
    return stored_query_db[dialect][query]


def generate_query(query_type, dialect='postgresql', query_data=None):
    # init
    if query_data.has_key('schm'):
        prfx = "{schm}.".format(**query_data) if dialect =='postgresql' else ""
    else: prfx = ""

    #queries
    if query_type == 'get_row':
        q0 = "SELECT * FROM {0}{tbl} WHERE {where} LIMIT 1".format(prfx, **query_data)
        return (q0,)

    elif query_type == 'browse_table':
        q0 = "SELECT * FROM {0}{tbl}"
        if query_data.has_key('sort_key') and query_data.has_key('sort_dir'):
            q0 += " ORDER BY {sort_key} {sort_dir}"
        q0 += " LIMIT {limit} OFFSET {offset}"
        return (q0.format(prfx, **query_data),)

    elif query_type == 'count_rows':
        q0 = "SELECT count(*) FROM {0}{tbl}".format(prfx, **query_data)
        return (q0,)

    elif query_type == 'drop_table':
        queries = []
        for where in query_data['conditions']:
            where['table'] = where['table'].replace("'", "")
            queries.append( "DROP TABLE {0}{table}".format(prfx, **where))
        return tuple(queries)
    
    elif query_type == 'empty_table':
        queries = []
        for where in query_data['conditions']:
            where['table'] = where['table'].replace("'", "")
            queries.append( "TRUNCATE {0}{table}".format(prfx, **where) )
        return tuple(queries)

    elif query_type == 'delete_row':
        queries = []
        for whereCond in query_data['where_stmt'].split(';'):
            q0 = "DELETE FROM {0}{tbl}".format(prfx, **query_data) + " WHERE "+whereCond
            queries.append(q0)
        return tuple(queries)

    elif dialect == 'postgresql': #postgresql-only statements
        
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
            queries = (q0, )
            return queries
        
        elif query_type == 'drop_user':
            queries = []
            for cond in query_data:
                q = "DROP ROLE {rolname}".format(**cond)
                queries.append(q) 
            return tuple(queries)
        
        elif query_type == 'create_db':
            _l = []
            _l.append("CREATE DATABASE {name}")
            if query_data['encoding']: _l.append(" WITH ENCODING='{encoding}'")
            if query_data['owner']: _l.append(" OWNER={owner}")
            if query_data['template']: _l.append(" TEMPLATE={template}")
            return ("".join(_l).format(**query_data), )
        
        elif query_type == 'table_rpr':
            q = "SELECT t2.tablename AS table, t2.tableowner AS owner, t2.tablespace, t1.reltuples::integer AS \"estimated row count\" \
FROM ( pg_catalog.pg_class as t1 INNER JOIN pg_catalog.pg_tables AS t2  ON t1.relname = t2.tablename) \
WHERE t2.schemaname='{schm}' ORDER BY t2.tablename ASC".format(**query_data)
            return (q, )
        
        elif query_type == 'indexes':
            q0 = "SELECT kcu.column_name, kcu.constraint_name, tc.constraint_type \
FROM information_schema.key_column_usage AS kcu LEFT OUTER JOIN information_schema.table_constraints \
AS tc on (kcu.constraint_name = tc.constraint_name) WHERE kcu.table_name='{tbl}' \
AND kcu.table_schema='{schm}' AND kcu.table_catalog='{db}'".format(**query_data)
            return (q0,)
        
        elif query_type == 'primary_keys':
            q0 = "SELECT kcu.column_name, kcu.constraint_name, tc.constraint_type \
FROM information_schema.key_column_usage AS kcu LEFT OUTER JOIN information_schema.table_constraints \
AS tc on (kcu.constraint_name = tc.constraint_name) WHERE kcu.table_name='{tbl}' \
AND kcu.table_schema='{schm}' AND kcu.table_catalog='{db}' AND \
(tc.constraint_type='PRIMARY KEY')".format(**query_data)
            return (q0, )
        
        elif query_type == 'table_structure':
            q0 = "SELECT column_name as column, data_type as type, is_nullable as null, \
column_default as default, character_maximum_length, numeric_precision, numeric_scale, \
datetime_precision, interval_type, interval_precision FROM information_schema.columns \
WHERE table_catalog='{db}' AND table_schema='{schm}' AND table_name='{tbl}' \
ORDER BY ordinal_position ASC".format(**query_data)
            return (q0, )
        
        elif query_type == 'table_sequences':
            q0 = 'SELECT sequence_name, nextval(sequence_name::regclass), \
setval(sequence_name::regclass, lastval() - 1, true) FROM information_schema.sequences'
            return (q0, )
        
        elif query_type == 'existing_tables':
            # selects both tables and views
#            q0 = "SELECT table_name FROM information_schema.tables WHERE table_schema='{schm}' \
#ORDER BY table_name ASC".format(**query_data)
            # selects only tables
            q0 = "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='{schm}' \
ORDER BY tablename ASC".format(**query_data)
            return (q0, )

        elif query_type == 'foreign_key_relation':
            q0 = 'SELECT conname, confrelid::regclass AS "referenced_table", \
conkey AS array_local_columns, confkey AS array_foreign_columns \
FROM pg_constraint WHERE contype = \'f\' AND conrelid::regclass = \'{tbl}\'::regclass \
AND connamespace = (SELECT oid from pg_namespace WHERE nspname=\'{schm}\') \
'.format(**query_data)
            return (q0, )
        
        
    elif dialect == 'mysql': # mysql-only statements

        if query_type == 'create_user':
            # create user statement
            queries = []
            q1 = "CREATE USER '{username}'@'{host}'".format(**query_data)
            if query_data['password']:
                q1 += " IDENTIFIED BY '{password}'".format(**query_data)
            
            queries.append(q1)
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
                    q3 = q2 + ' ON {db}.*'.format(database = db)
                    # user specification
                    q3 += " TO '{username}'@'{host}'".format(**query_data)
                    # grant option
                    if query_data['options']:
                        q3 += " WITH {options[0]}".format(**query_data)
                    # append generated query to queries
                    queries.append(q3)
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
                queries.append(q4)
            return tuple( queries )
        
        elif query_type == 'create_db':
            q = "CREATE DATABASE {name}".format(**query_data)
            if query_data['charset']:
                q += " CHARACTER SET {charset}".format(**query_data)
            return (q, )
        
        elif query_type == 'column_list':
            return ("SELECT column_name FROM information_schema.columns WHERE table_schema='{db}' AND table_name='{tbl}'")
        
        elif query_type == 'drop_user':
            queries = []
            for where in query_data:
                q = "DROP USER '{user}'@'{host}'".format(**where)
                queries.append(q)
            return tuple(queries)
        
        elif query_type == 'table_rpr':
            q = "SELECT TABLE_NAME AS 'table', TABLE_ROWS AS 'rows', TABLE_TYPE AS 'type', ENGINE FROM \
            `INFORMATION_SCHEMA`.`TABLES` WHERE TABLE_SCHEMA = '{db}'".format(**query_data)
            return (q,)
        
        elif query_type == 'indexes':
            q0 = "SELECT DISTINCT kcu.column_name, kcu.constraint_name, tc.constraint_type \
from information_schema.key_column_usage as kcu, information_schema.table_constraints as tc WHERE \
kcu.constraint_name = tc.constraint_name AND kcu.table_schema='{db}' AND tc.table_schema='{db}' \
AND kcu.table_name='{tbl}'".format(**query_data)
            return (q0, )
        
        elif query_type == 'primary_keys':
            q0 = "SELECT DISTINCT kcu.column_name, kcu.constraint_name, tc.constraint_type \
from information_schema.key_column_usage as kcu, information_schema.table_constraints as tc WHERE \
kcu.constraint_name = tc.constraint_name AND kcu.table_schema='{db}' AND tc.table_schema='{db}' \
AND kcu.table_name='{tbl}' AND tc.table_name='{tbl}' \
AND (tc.constraint_type='PRIMARY KEY')".format(**query_data)
            return (q0, )
        
        elif query_type == 'table_structure':
            q0 = 'SELECT column_name AS "column", column_type AS "type", is_nullable AS "null", \
column_default AS "default", extra \
FROM information_schema.columns WHERE table_schema="{db}" AND table_name="{tbl}" \
ORDER BY ordinal_position ASC'.format(**query_data)
            return (q0, )

        elif query_type == 'raw_table_structure':
            q0 = 'SELECT column_name AS "column", data_type AS "type", is_nullable AS "null", \
column_default AS "default", character_maximum_length, numeric_precision, numeric_scale, extra, column_type \
FROM information_schema.columns WHERE table_schema="{db}" AND table_name="{tbl}" \
ORDER BY ordinal_position ASC'.format(**query_data)
            return (q0, )
        
        elif query_type == 'existing_tables':
            q0 = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{db}'".format(**query_data)
            return (q0, )
        


def full_query(conn_params, query):
    '''
    executes and returns a query result
    '''
    eng = create_engine(get_conn_link(conn_params))
    conn = eng.connect()
    try:
        conn = eng.connect()
        query_result =  conn.execute(text(query))
        d = {}
        l = []
        for row in query_result:
            row = list(row)
            for i in range(len(row)):
                if row[i] == None:
                    row[i] = ""
                elif type( row[i] ) == datetime.datetime:
                    row[i] = row[i].__str__()
            l.append( tuple(row) )
        d =  {'columns': query_result.keys(),'count': query_result.rowcount, 
            'rows': l}
        conn.close()
        return d
    except Exception as e:
        conn.close()
        return str(e)
    
    
def short_query(conn_params, queries):
    """
    executes and returns the success state of the query
    """
    eng = create_engine( get_conn_link(conn_params) )
    conn = ''
    try:
        conn = eng.connect()
        for query in queries:
            query_result = conn.execute(text(query))
        return {'status':'success', 'msg':''}
    except Exception as e:
        conn.close()
        return {'status':'fail', 'msg': str(e) }
    
    
def model_login(conn_params):
    link = URL(conn_params['database_driver'], username = conn_params['username'],
        password= conn_params['password'], host = conn_params['host'])
    if conn_params['connection_database']:
        link.database = conn_params['connection_database']
    elif not conn_params['connection_database'] and conn_params['database_driver'] == 'postgresql':
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
 


def get_conn_link(conn_params):
    return '{dialect}://{username}:{password}@{host}/{db}'.format(**conn_params)


