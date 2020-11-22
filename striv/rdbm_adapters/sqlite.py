from sqlite3 import connect

ENTITY_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS entities (
    typed_id TEXT PRIMARY KEY,
    sortkey TEXT,
    entity TEXT
)
'''
SORTKEY_INDEX_DEF = '''
CREATE INDEX IF NOT EXISTS sortkey ON entities (sortkey)
'''
RELATION_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS relations (
    typed_id TEXT,
    relation TEXT,
    secondary_key TEXT
)
'''
RELATION_INDEX_DEF = '''
CREATE INDEX IF NOT EXISTS lookup ON relations (relation, secondary_key)
'''


def connection(connargs):
    conn = connect(**connargs)
    conn.isolation_level = None
    return conn


def ensure_ddl(conn):
    conn.cursor().execute(ENTITY_TABLE_DEF)
    conn.cursor().execute(SORTKEY_INDEX_DEF)
    conn.cursor().execute(RELATION_TABLE_DEF)
    conn.cursor().execute(RELATION_INDEX_DEF)
