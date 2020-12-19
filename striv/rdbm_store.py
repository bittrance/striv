import json
from striv.errors import EntityNotFound

CONN = None
DRIVER = None
RELATIONS = {}  # pylint: disable = dangerous-default-value
SORTKEYS = {}  # pylint: disable = dangerous-default-value


def _cursor():
    return CONN.cursor()


def _maybe_qm(source):
    if DRIVER == 'sqlite':
        return source.replace('%s', '?')
    return source


def _prepare_entities(entities):
    for (typ, eid, entity) in entities:
        yield (
            '%s:%s' % (typ, eid),
            SORTKEYS[typ](entity) if typ in SORTKEYS else None,
            json.dumps(entity)
        )


def _relation_keys(entities):
    for (typ, eid, entity) in entities:
        if typ in RELATIONS:
            for (relation, key) in RELATIONS[typ](entity):
                yield ('%s:%s' % (typ, eid), relation, key)


# pylint: disable = import-outside-toplevel
def setup(driver, connargs, relations=None, sortkeys=None):
    '''
    Setup the sqlite store. Defaults to creating an in-memory store.
    '''
    global CONN, DRIVER, RELATIONS, SORTKEYS
    RELATIONS.update(relations or {})
    SORTKEYS.update(sortkeys or {})
    if driver == 'mysql':
        from striv.rdbm_adapters import mysql
        adapter = mysql
    elif driver == 'postgres':
        from striv.rdbm_adapters import postgres
        adapter = postgres
    elif driver == 'sqlite':
        from striv.rdbm_adapters import sqlite
        adapter = sqlite
    else:
        raise RuntimeError('Unknown database driver %s' % driver)
    CONN = adapter.connection(connargs)
    adapter.ensure_ddl(CONN)
    DRIVER = driver


def load_entities(*query):
    '''
    Load a series of entities from the store. The query is a list of
    (type, id) tuples. Entities are guaranteed to be returned in the
    order they were queried and loading will fail if one or more tuples
    fail to retrieve an entity.
    '''
    typed_ids = ['%s:%s' % (typ, eid) for (typ, eid) in query]
    qs = ','.join(['%s'] * len(typed_ids))
    cur = _cursor()
    cur.execute(
        _maybe_qm(
            'SELECT typed_id, entity FROM entities WHERE typed_id IN (%s)' % qs),
        typed_ids
    )
    candidates = {}
    for (typed_id, entity) in cur:
        candidates[typed_id] = json.loads(entity)
    entities = []
    for typed_id in typed_ids:
        try:
            entities.append(candidates[typed_id])
        except KeyError as err:
            raise EntityNotFound(typed_id) from err
    return entities


def find_entities(typ, related_to=None, limit=None, range=None):
    '''
    Retrieve all entities of a particular type. Returns a dict mapping
    id to entity. related_to is a (relation, key) tuple and can be used
    to scope the result to just a single relation. limit can be used to
    constrain the number of returned results. range is a (asc | desc,
    inclusive lower, inclusive upper) tuple which returns a slice of
    entities in a certain sort order.
    '''
    if related_to:
        flter = 'typed_id IN (SELECT typed_id FROM relations WHERE relation = %s AND secondary_key = %s)'
        args = [*related_to]
    else:
        flter = 'typed_id LIKE %s'
        args = ['%s:%%' % typ]
    query = 'SELECT typed_id, entity FROM entities WHERE %s' % flter
    if range is not None:
        order, lower, upper = range
        assert order.upper() in ['ASC', 'DESC']
        if lower is not None:
            query += ' AND sortkey >= %s'
            args += [lower]
        if upper is not None:
            query += ' AND sortkey <= %s'
            args += [upper]
        query += ' ORDER BY sortkey %s' % order
    if limit is not None:
        query += ' LIMIT %d' % limit
    cur = _cursor()
    cur.execute(_maybe_qm(query), args)
    return dict((typed_id[len(typ) + 1:], json.loads(entity)) for (typed_id, entity) in cur)


def upsert_entities(*entities):
    '''
    Store entities in the store, overwriting any previous entity with
    the same eid. Input is a series of (type, id, entity). Entity is any
    jsonable value. Updates relations indexes as defined in the relations
    argument passed to setup.
    '''
    if DRIVER == 'mysql':
        replace_entities = '''
        INSERT INTO entities (typed_id, sortkey, entity) VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE sortkey = VALUES(sortkey), entity = VALUES(entity)
        '''
    else:
        replace_entities = '''
        INSERT INTO entities (typed_id, sortkey, entity) VALUES (%s, %s, %s)
        ON CONFLICT(typed_id)
        DO UPDATE SET sortkey = excluded.sortkey, entity = excluded.entity
        '''
    old_relations = '''
    DELETE FROM relations WHERE typed_id = %s
    '''
    new_relations = '''
    INSERT INTO relations (typed_id, relation, secondary_key) VALUES (%s, %s, %s)
    '''
    ids = (('%s:%s' % (typ, eid),) for (typ, eid, _) in entities)
    _cursor().executemany(_maybe_qm(replace_entities), list(_prepare_entities(entities)))
    _cursor().executemany(_maybe_qm(old_relations), list(ids))
    _cursor().executemany(_maybe_qm(new_relations), list(_relation_keys(entities)))


def delete_entities(*query):
    '''
    Delete entities from the store. The query is a list of (type, id) 
    tuples. Raises EntityNotFound when asked to delete non-existent entities.
    '''
    load_entities(*query)
    delete_entities = 'DELETE FROM entities WHERE typed_id = %s'
    delete_relations = 'DELETE FROM relations WHERE typed_id = %s'
    ids = [('%s:%s' % (typ, eid),) for (typ, eid) in query]
    _cursor().executemany(_maybe_qm(delete_entities), ids)
    _cursor().executemany(_maybe_qm(delete_relations), ids)


# TODO: replace_type needs to know what index to chuck out
def replace_type(typ, entities):
    '''
    Drop all entities of one type, and replace them with the provided
    list.
    '''
    delete_cur = _cursor()
    delete_cur.execute(
        _maybe_qm('DELETE FROM entities WHERE typed_id LIKE %s'),
        [typ + ':%']
    )
    rows = (('%s:%s' % (typ, eid), json.dumps(entity))
            for (eid, entity) in entities.items())
    insert_cur = _cursor()
    insert_cur.executemany(
        _maybe_qm('INSERT INTO entities (typed_id, entity) VALUES (%s, %s)'),
        list(rows)
    )
    return (delete_cur.rowcount, insert_cur.rowcount)
