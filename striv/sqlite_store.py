import json
import sqlite3

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

CONN = None
SORTKEYS = {}  # pylint: disable = dangerous-default-value


def _cursor():
    return CONN.cursor()


def setup(database=':memory:', sortkeys={}):
    '''
    Setup the sqlite store. Defaults to creating an in-memory store.
    '''
    global CONN, SORTKEYS
    SORTKEYS.update(sortkeys)
    CONN = sqlite3.connect(database)
    CONN.isolation_level = None
    _cursor().execute(ENTITY_TABLE_DEF)
    _cursor().execute(SORTKEY_INDEX_DEF)


def load_entities(*query):
    '''
    Load a series of entities from the store. The query is a list of
    (type, id) tuples. Entities are guaranteed to be returned in the
    order they were queried and loading will fail if one or more tuples
    fail to retrieve an entity.
    '''
    typed_ids = ['%s:%s' % (typ, eid) for (typ, eid) in query]
    qs = ','.join('?' * len(typed_ids))
    result = _cursor().execute(
        'SELECT typed_id, entity FROM entities WHERE typed_id IN (%s)' % qs,
        typed_ids
    )
    candidates = {}
    for (typed_id, entity) in result:
        candidates[typed_id] = json.loads(entity)
    entities = []
    for typed_id in typed_ids:
        entities.append(candidates[typed_id])
    return entities


def find_entities(typ, limit=None, range=None):
    '''
    Retrieve all entities of a particular type. Returns a dict mapping
    id to entity. limit can be used to constrain the number of returned
    results. range is a (asc | desc, inclusive lower, inclusive upper)
    tuple which returns a slice of entities in a certain sort order.
    '''
    query = 'SELECT typed_id, entity FROM entities WHERE typed_id LIKE ?'
    args = ['%s:%%' % typ]
    if range is not None:
        order, lower, upper = range
        assert order.upper() in ['ASC', 'DESC']
        if lower is not None:
            query += ' AND sortkey >= ?'
            args += [lower]
        if upper is not None:
            query += ' AND sortkey <= ?'
            args += [upper]
        query += ' ORDER BY sortkey %s' % order
    if limit is not None:
        query += ' LIMIT %d' % limit
    result = _cursor().execute(query, args)
    return dict((typed_id[len(typ) + 1:], json.loads(entity)) for (typed_id, entity) in result)


def upsert_entities(*entities):
    '''
    Store entities in the store, overwriting any previous entity with
    the same eid. Input is a series of (type, id, entity). Entity is any 
    jsonable value.
    '''
    insert = '''
    INSERT INTO entities (typed_id, sortkey, entity) VALUES (?, ?, ?)
    ON CONFLICT(typed_id)
    DO UPDATE SET sortkey = excluded.sortkey, entity = excluded.entity
    '''
    rows = ([
        '%s:%s' % (typ, eid),
        SORTKEYS[typ](entity) if typ in SORTKEYS else None,
        json.dumps(entity)
    ] for (typ, eid, entity) in entities)
    _cursor().executemany(insert, rows)


def replace_type(typ, entities):
    '''
    Drop all entities of one type, and replace them with the provided
    list.
    '''
    delete_res = _cursor().execute(
        'DELETE FROM entities WHERE typed_id LIKE ?',
        [typ + ':%']
    )
    insert = 'INSERT INTO entities (typed_id, entity) VALUES (?, ?)'
    rows = (('%s:%s' % (typ, eid), json.dumps(entity))
            for (eid, entity) in entities.items())
    insert_res = _cursor().executemany(insert, rows)
    return (delete_res.rowcount, insert_res.rowcount)
