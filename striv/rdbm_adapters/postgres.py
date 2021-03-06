from psycopg2 import connect, errors

ENTITY_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS entities (
    typed_id VARCHAR(128) PRIMARY KEY,
    sortkey VARCHAR(128),
    entity TEXT
)
'''
SORTKEY_INDEX_DEF = '''
CREATE INDEX IF NOT EXISTS sortkey ON entities (sortkey)
'''
RELATION_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS relations (
    typed_id VARCHAR(128),
    relation VARCHAR(128),
    secondary_key VARCHAR(128)
)
'''
RELATION_INDEX_DEF = '''
CREATE INDEX IF NOT EXISTS lookup ON relations (relation, secondary_key)
'''


def connection(connargs):
    if connargs.pop('create_database', False):
        ensure_database(connargs)
    conn = connect(**connargs)
    conn.autocommit = True
    return conn


def ensure_database(connargs):
    props = connargs.copy()
    db = props.pop('dbname')
    conn = connect(**props)
    conn.autocommit = True
    try:
        conn.cursor().execute('CREATE DATABASE %s' % db)
    except errors.DuplicateDatabase:
        pass


def ensure_ddl(conn):
    conn.cursor().execute(ENTITY_TABLE_DEF)
    conn.cursor().execute(SORTKEY_INDEX_DEF)
    conn.cursor().execute(RELATION_TABLE_DEF)
    conn.cursor().execute(RELATION_INDEX_DEF)
