# pylint: disable = missing-function-docstring, redefined-outer-name
import pytest

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import sqlite_store


@pytest.fixture()
def store():
    sqlite_store.setup()
    return sqlite_store


def test_roundtrip_sorted(store):
    store.store_entity('job', 'foo', {'id': 'foo'})
    store.store_entity('job', 'bar', {'id': 'bar'})
    entities = store.load_entities(('job', 'foo'), ('job', 'bar'))
    assert entities == [{'id': 'foo'}, {'id': 'bar'}]
    entities = store.load_entities(('job', 'bar'), ('job', 'foo'))
    assert entities == [{'id': 'bar'}, {'id': 'foo'}]


def test_fails_on_missing(store):
    store.store_entity('job', 'foo', {'id': 'foo'})
    store.store_entity('job', 'bar', {'id': 'bar'})
    assert_that(
        calling(store.load_entities)
        .with_args(('job', 'foo'), ('job', 'baz')),
        raises(KeyError, pattern='job:baz')
    )
