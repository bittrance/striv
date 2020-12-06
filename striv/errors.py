class EntityNotFound(Exception):
    '''
    Store could not locate the requested entity.
    '''

    def __init__(self, eid):
        super(EntityNotFound, self).__init__('No entity %s found' % eid)
        self.eid = eid


class RunNotFound(RuntimeError):
    '''
    Requested run was not found in logstore.
    '''
