import json
import sqlite3

ENTITY_TABLE_DEF = '''
CREATE TABLE IF NOT EXISTS entities (
    typed_id TEXT,
    entity TEXT
)
'''

CONN = None


def _cursor():
    return CONN.cursor()


def setup(database=':memory:'):
    '''
    Setup the sqlite store. Defaults to creating an in-memory store.
    '''
    global CONN
    CONN = sqlite3.connect(database)
    CONN.isolation_level = None
    _cursor().execute(ENTITY_TABLE_DEF)


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


def find_entities(typ):
    '''
    Retrieve all entities of a particular type. Returns a dict
    mapping id to entity.
    '''
    result = _cursor().execute(
        'SELECT typed_id, entity FROM entities WHERE typed_id LIKE ?',
        ['%s:%%' % typ]
    )
    return dict((typed_id[len(typ) + 1:], json.loads(entity)) for (typed_id, entity) in result)


def store_entity(typ, eid, entity):
    '''
    Store an entity in the store. Entity is any jsonable value.
    '''
    insert = 'INSERT INTO entities (typed_id, entity) VALUES (?, ?)'
    _cursor().execute(insert, ['%s:%s' % (typ, eid), json.dumps(entity)])


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
