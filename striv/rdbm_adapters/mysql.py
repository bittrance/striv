from mysql.connector import connect, errors

ENTITY_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS entities (
    typed_id VARCHAR(128) PRIMARY KEY,
    sortkey VARCHAR(128),
    entity TEXT
)
'''
SORTKEY_INDEX_DEF = '''
CREATE INDEX sortkey ON entities (sortkey)
'''
RELATION_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS relations (
    typed_id VARCHAR(128),
    relation VARCHAR(128),
    secondary_key VARCHAR(128)
)
'''
RELATION_INDEX_DEF = '''
CREATE INDEX lookup ON relations (relation, secondary_key)
'''


def connection(connargs):
    if connargs.pop('create_database', False):
        ensure_database(connargs)
    conn = connect(**connargs)
    conn.autocommit = True
    return conn


def ensure_database(connargs):
    props = connargs.copy()
    db = props.pop('database')
    c = connect(**props)
    c.cursor().execute('CREATE DATABASE IF NOT EXISTS %s' % db)


def ensure_ddl(conn):
    conn.cursor().execute(ENTITY_TABLE_DEF)
    try:
        conn.cursor().execute(SORTKEY_INDEX_DEF)
    except errors.ProgrammingError as err:
        if err.errno != 1061:
            raise err
    conn.cursor().execute(RELATION_TABLE_DEF)
    try:
        conn.cursor().execute(RELATION_INDEX_DEF)
    except errors.ProgrammingError as err:
        if err.errno != 1061:
            raise err
