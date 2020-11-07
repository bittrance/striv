# pylint: disable = missing-function-docstring, no-self-use, redefined-outer-name
import pytest

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import sqlite_store


@pytest.fixture()
def store():
    sqlite_store.setup(sortkeys={
        'job': lambda job: job['name'],
    })
    return sqlite_store


@pytest.fixture()
def five_jobs(store):
    store.upsert_entities(
        *[('job', 'job-%02d' % n, {'name': 'job-%02d' % n}) for n in range(1, 6)])


def test_roundtrip_sorted(store):
    store.upsert_entities(('job', 'foo', {'name': 'foo'}))
    store.upsert_entities(('job', 'bar', {'name': 'bar'}))
    entities = store.load_entities(('job', 'foo'), ('job', 'bar'))
    assert entities == [{'name': 'foo'}, {'name': 'bar'}]
    entities = store.load_entities(('job', 'bar'), ('job', 'foo'))
    assert entities == [{'name': 'bar'}, {'name': 'foo'}]


def test_fails_on_missing(store):
    store.upsert_entities(('job', 'foo', {'name': 'foo'}))
    store.upsert_entities(('job', 'bar', {'name': 'bar'}))
    assert_that(
        calling(store.load_entities)
        .with_args(('job', 'foo'), ('job', 'baz')),
        raises(KeyError, pattern='job:baz')
    )


@pytest.mark.usefixtures('five_jobs')
class TestFindEntities:
    def test_returns_all_entities(self, store):
        found = store.find_entities('job')
        assert found.keys() == {'job-01', 'job-02',
                                'job-03', 'job-04', 'job-05'}

    def test_find_entitites_paginates(self, store):
        found = store.find_entities('job', limit=3)
        assert found.keys() == {'job-01', 'job-02', 'job-03'}

    def test_returns_ranges_on_sortkey_with_lower_bound(self, store):
        found = store.find_entities('job', range=('desc', 'job-03', None))
        assert found.keys() == {'job-03', 'job-04', 'job-05'}

    def test_returns_ranges_on_sortkey_with_upper_bound(self, store):
        found = store.find_entities('job', range=('desc', None, 'job-03'))
        assert found.keys() == {'job-01', 'job-02', 'job-03'}

    def test_returns_ranges_on_sortkey_with_middle_bound(self, store):
        found = store.find_entities('job', range=('desc', 'job-02', 'job-04'))
        assert found.keys() == {'job-02', 'job-03', 'job-04'}

    def test_returns_ranges_on_sortkey_with_empty_range(self, store):
        found = store.find_entities('job', range=('desc', 'job-10', None))
        assert list(found) == []

    def test_paginates_ranges_descending(self, store):
        found = store.find_entities(
            'job',
            range=('desc', 'job-01', 'job-06'),
            limit=3
        )
        assert found.keys() == {'job-05', 'job-04', 'job-03'}

    def test_paginates_ranges_ascending(self, store):
        found = store.find_entities(
            'job',
            range=('asc', 'job-01', 'job-06'),
            limit=3
        )
        assert found.keys() == {'job-01', 'job-02', 'job-03'}

    def test_arbitrary_chars_in_range(self, store):
        found = store.find_entities('job', range=('desc', None, ';'))
        assert list(found) == []
        found = store.find_entities('job', range=('desc', None, "'"))
        assert list(found) == []


def test_upsert_entities_updates_sortkey(store):
    store.upsert_entities(('job', 'foo', {'name': 'foo'}))
    store.upsert_entities(('job', 'foo', {'name': 'bar'}))
    found = store.find_entities('job', range=('asc', None, 'bar'))
    assert found.keys() == {'foo'}
