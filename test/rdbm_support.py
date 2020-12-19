import os
import uuid

configurations = [
    [
        'mysql',
        {
            'user': 'root',
            'password': 'Cmdu1OG2vLfL',
            'host': '127.0.0.1',
            'database': 'striv_test',
            'create_database': True,
        }
    ],
    [
        'postgres',
        {
            'user': 'striv',
            'password': 'Cmdu1OG2vLfL',
            'host': '127.0.0.1',
            'dbname': 'striv_test',
            'create_database': True,
        }
    ],
    [
        'sqlite',
        {
            'database': ':memory:'
        }
    ],
]

filtered_stores = os.environ.get('STORES')
if filtered_stores:
    configurations = [c for c in configurations if c[0]
                      in filtered_stores.split(',')]
