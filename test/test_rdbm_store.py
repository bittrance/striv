# pylint: disable = missing-class-docstring, missing-function-docstring, no-self-use, redefined-outer-name
import pytest

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import rdbm_store
from striv.errors import EntityNotFound

from . import rdbm_support


@pytest.fixture(params=rdbm_support.configurations)
def store(request):
    driver, connargs = request.param
    rdbm_store.setup(
        driver,
        connargs,
        relations={
            'run': lambda run: [('job', run['job_id'])],
            'job': lambda job: [('dvalue', '%s:%s' % (n, v)) for (n, v) in job.get('dimensions', {}).items()]
        },
        sortkeys={
            'job': lambda job: job['name'],
        }
    )
    yield rdbm_store
    # TODO: Teach replace_type about relations
    rdbm_store.CONN.cursor().execute('DELETE FROM entities')
    rdbm_store.CONN.cursor().execute('DELETE FROM relations')


@pytest.fixture()
def five_jobs(store):
    store.upsert_entities(
        *[(
            'job',
            'job-%02d' % n,
            {
                'name': 'job-%02d' % n,
                'dimensions': {
                    'shared': 'value-%d' % (n % 2),
                    'unique': 'value-%d' % n,
                }
            }
        ) for n in range(1, 6)]
    )


@pytest.mark.usefixtures('five_jobs')
class TestLoadEntities:
    def test_roundtrip_sorted(self, store):
        entities = store.load_entities(('job', 'job-01'), ('job', 'job-02'))
        assert_that(
            entities,
            contains_exactly(
                has_entry('name', 'job-01'),
                has_entry('name', 'job-02'),
            )
        )
        entities = store.load_entities(('job', 'job-02'), ('job', 'job-01'))
        assert_that(
            entities,
            contains_exactly(
                has_entry('name', 'job-02'),
                has_entry('name', 'job-01'),
            )
        )

    def test_fails_on_missing(self, store):
        assert_that(
            calling(store.load_entities)
            .with_args(('job', 'job-01'), ('job', 'job-10')),
            raises(EntityNotFound, pattern='job:job-10')
        )


@pytest.mark.usefixtures('five_jobs')
class TestFindEntities:
    def test_returns_all_entities(self, store):
        found = store.find_entities('job')
        assert found.keys() == {'job-01', 'job-02',
                                'job-03', 'job-04', 'job-05'}

    def test_related_to_returns_only_related(self, store):
        found = store.find_entities(
            'job', related_to=('dvalue', 'unique:value-1'))
        assert found.keys() == {'job-01'}

    def test_related_to_can_produce_empty_result(self, store):
        found = store.find_entities(
            'job', related_to=('dvalue', 'unique:value-10'))
        assert list(found) == []

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

    def test_related_to_and_range_cooperates(self, store):
        found = store.find_entities(
            'job',
            related_to=('dvalue', 'shared:value-1'),
            range=('desc', 'job-01', 'job-03')
        )
        assert found.keys() == {'job-01', 'job-03'}

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


@pytest.mark.usefixtures('five_jobs')
def test_upsert_entities_updates_sortkey(store):
    store.upsert_entities(('job', 'job-01', {'name': 'job-00'}))
    found = store.find_entities('job', range=('asc', None, 'job-00'))
    assert found.keys() == {'job-01'}
