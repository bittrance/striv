import fetchMock from 'fetch-mock-jest'
import store from '@/store.js'

describe('actions', () => {
    let evaluation = { payload: { some: 'payload' } }
    let job = { name: 'ze-name', execution: 'ze-execution' }
    let run1 = {
        job_id: 'job-1',
        status: 'pending',
        created_at: '2020-10-31T23:40:40+0000',
    }
    let run2 = {
        job_id: 'job-1',
        status: 'successful',
        created_at: '2020-10-31T23:40:41+0000',
        started_at: '2020-10-31T23:40:01+0000',
        finished_at: '2020-10-31T23:40:05+0000',
    }
    let logs1 = { 'some': 'log' }

    beforeEach(() => fetchMock.mockReset())

    describe('current_job', () => {
        it('commits the new job and the evaluated evaluation', async () => {
            fetchMock.post('path:/api/jobs/evaluate', evaluation)
            let commit = jest.fn()
            await store.actions.current_job({ commit }, job)
            expect(commit).toHaveBeenCalledWith('current_job', job)
            expect(commit).toHaveBeenCalledWith('current_job_evaluation', evaluation)
        })
    })

    describe('load_job', () => {
        let commit

        beforeEach(async () => {
            let my_job = Object.assign({}, job)
            my_job.modified_at = '2020-10-31T23:40:00+0000'
            fetchMock.get('path:/api/job/job-1', my_job)
            commit = jest.fn()
            await store.actions.load_job({ commit }, 'job-1')
        })

        it('loads a single job', async () => {
            expect(commit).toHaveBeenCalledWith(
                'current_job',
                expect.objectContaining({ name: 'ze-name' })
            )
            expect(commit).toHaveBeenCalledWith('current_job_id', 'job-1')
        })

        it('converts ISO date strings to date objects', () => {
            expect(commit).toHaveBeenCalledWith(
                'current_job',
                expect.objectContaining({ modified_at: expect.any(Date) })
            )
        })
    })

    describe('load_jobs', () => {
        let commit

        beforeEach(async () => {
            let my_job = Object.assign({}, job)
            my_job.modified_at = '2020-10-31T23:40:00+0000'
            fetchMock.get('path:/api/jobs', { 'job-1': my_job })
            commit = jest.fn()
            await store.actions.load_jobs({ commit })
        })

        it('loads a single job', async () => {
            expect(commit).toHaveBeenCalledWith(
                'load_jobs',
                expect.objectContaining({
                    'job-1': expect.objectContaining({ modified_at: expect.any(Date) })
                })
            )
        })
    })

    describe('store_current_job', () => {
        let tools = { state: { current_job: job } }

        it('persists the current job as a new job', async () => {
            fetchMock.post('path:/api/jobs', job)
            await store.actions.store_current_job(tools)
            expect(fetchMock).toHaveFetched((url, req) => {
                expect(JSON.parse(req.body)).toHaveProperty('name', 'ze-name')
                return true
            })
        })

        describe('when current job id is known', () => {
            let tools = {
                state: {
                    current_job: job,
                    current_job_id: 'job-1',
                }
            }

            it('updates the existing job', async () => {
                fetchMock.put('path:/api/job/job-1', '')
                await store.actions.store_current_job(tools)
                expect(fetchMock).toHaveFetched()
            })
        })
    })

    describe('load_runs and load_job_runs', () => {
        let commit

        beforeEach(async () => {
            commit = jest.fn()
            fetchMock.get('path:/api/runs', { 'run-1': run1, 'run-2': run2 })
            await store.actions.load_runs({ commit })
        })

        it('loads the runs', () => {
            expect(commit).toHaveBeenCalledWith(
                'load_runs',
                expect.objectContaining({
                    'run-1': expect.anything(),
                    'run-2': expect.anything(),
                })
            )
        })

        it('converts ISO date strings to date objects', () => {
            expect(commit).toHaveBeenCalledWith(
                'load_runs',
                expect.objectContaining({
                    'run-2': expect.objectContaining({
                        created_at: expect.any(Date),
                        started_at: expect.any(Date),
                        finished_at: expect.any(Date),
                    })
                })
            )
        })

        it('calculates duration for completed jobs', () => {
            let runs = commit.mock.calls[0][1]
            expect(runs['run-2']).toHaveProperty('duration', '1m')
        })
    })

    describe('load_run', () => {
        let commit

        beforeEach(async () => {
            commit = jest.fn()
            fetchMock.get('path:/api/run/run-1', run1)
            fetchMock.get('path:/api/run/run-1/logs', logs1)
            fetchMock.get('path:/api/job/job-1', job)
            await store.actions.load_run({ commit }, 'run-1')
        })

        it('commits the run and its logs', () => {
            expect(commit).toHaveBeenCalledWith(
                'current_run',
                expect.objectContaining({
                    status: 'pending',
                    created_at: expect.any(Date),
                })
            )
            expect(commit).toHaveBeenCalledWith('current_run_logs', logs1)
        })

        it('commits the runs job and job id', () => {
            expect(commit).toHaveBeenCalledWith(
                'current_job',
                expect.objectContaining({ name: 'ze-name' })
            )
            expect(commit).toHaveBeenCalledWith('current_job_id', 'job-1')
        })

        it('converts ISO date strings to date objects', () => {
            expect(commit).toHaveBeenCalledWith(
                'current_run',
                expect.objectContaining({ created_at: expect.any(Date) })
            )
        })
    })
})