pending_alloc = {
    'ID': 'alloc-1',
    'JobID': 'job-1/periodic-123',
    'ClientStatus': 'pending',
    'TaskStates': {
        'task-1': {
            'State': 'pending',
            'Events': []
        }
    },
    'CreateTime': 1604187600012715000,
}

running_alloc = {
    'ID': 'alloc-2',
    'JobID': 'job-2',
    'ClientStatus': 'running',
    'TaskStates': {
        'task-1': {
            'State': 'running',
            'Events': [
                {'Type': 'Started', 'Time': 1604187602012715000},
            ]
        }
    },
    'CreateTime': 1604187600012715000,
}

rerunning_alloc = {
    'ID': 'alloc-3',
    'JobID': 'job-3',
    'ClientStatus': 'pending',
    'TaskStates': {
        'task-1': {
            'State': 'pending',
            'Events': [
                {'Type': 'Started', 'Time': 1604187602012715000},
                {'Type': 'Terminated', 'Time': 1604187603012715000},
                {'Type': 'Restarting', 'Time': 1604187603012715000},
                {'Type': 'Started', 'Time': 1604187604012715000},
            ]
        }
    },
    'CreateTime': 1604187600012715000,
}

successful_alloc = {
    'ID': 'alloc-4',
    'JobID': 'job-4',
    'ClientStatus': 'complete',
    'TaskStates': {
        'task-1': {
            'State': 'running',
            'Events': [
                {'Type': 'Started', 'Time': 1604187602012715000},
            ]
        }
    },
    'CreateTime': 1604187600012715000,
    'ModifyTime': 1604187605012715000,
}

failed_alloc = {
    'ID': 'alloc-5',
    'JobID': 'job-5',
    'ClientStatus': 'failed',
    'TaskStates': {
        'task-1': {
            'State': 'running',
            'Events': [
                {'Type': 'Started', 'Time': 1604187602012715000},
            ]
        }
    },
    'CreateTime': 1604187600012715000,
    'ModifyTime': 1604187605012715000,
}
