import pytest
import requests_mock

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import archivist


run_1 = {'status': 'running', 'created_at': '2020-10-31T23:40:02+0000'}
run_2 = {'status': 'successful', 'created_at': '2020-10-31T23:40:01+0000'}
run_3 = {'status': 'failed', 'created_at': '2020-10-31T23:40:00+0000'}
run_4 = {'status': 'running', 'created_at': '2020-10-31T23:39:00+0000'}


@pytest.fixture
def striv():
    with requests_mock.Mocker() as mock:
        yield mock


class TestRunsSince:
    def test_it_follows_link_headers(self, striv):
        striv.get(
            '/runs?lower=2020-10-31T23:40:00+0000',
            headers={'Link': '</runs?page_token=ze-token>; rel="next"'},
            json={'run-1': run_1, 'run-2': run_2}
        )
        striv.get(
            '/runs?page_token=ze-token',
            json={'run-3': run_3}
        )
        assert len(list(archivist.runs_since('http://localhost',
                                             '2020-10-31T23:40:00+0000'))) == 3


class TestUniqueFinishedRuns:
    def test_run_reported_only_when_finished(self):
        filter = archivist.UniqueFinishedRuns()
        assert list(filter.process([('run-1', run_1)])) == []
        assert list(filter.process([('run-2', run_2)])) == [('run-2', run_2)]

    def test_emits_finished_run_once(self):
        filter = archivist.UniqueFinishedRuns()
        assert list(filter.process([('run-2', run_2)])) == [('run-2', run_2)]
        assert list(filter.process([('run-2', run_2)])) == []

    def test_finished_runs_are_pruned_from_memory(self):
        filter = archivist.UniqueFinishedRuns()
        output = list(filter.process([('run-1', run_1), ('run-2', run_2)]))
        assert output == [('run-2', run_2)]


class TestOldestUnfinishedRun:
    def test_forwards_input(self):
        filter = archivist.OldestUnfinishedRun()
        input = [('run-1', run_1), ('run-4', run_4)]
        output = list(filter.process(input))
        assert input == output

    def test_no_oldest_when_no_input(self):
        filter = archivist.OldestUnfinishedRun()
        filter.process([])
        assert filter.next_start() == None

    def test_only_finished_runs(self):
        filter = archivist.OldestUnfinishedRun()
        list(filter.process([('run-3', run_3)]))
        assert filter.next_start() == '2020-10-31T23:40:00+0000'

    def test_oldest_unfinished_runs(self):
        filter = archivist.OldestUnfinishedRun()
        list(filter.process([('run-1', run_1), ('run-4', run_4)]))
        assert filter.next_start() == '2020-10-31T23:39:00+0000'
