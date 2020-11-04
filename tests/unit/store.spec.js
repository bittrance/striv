import fetchMock from 'fetch-mock-jest'
import store from '@/store.js'

describe('actions', () => {
    let evaluation = { payload: { some: 'payload' } }
    let job = { name: 'ze-name', execution: 'ze-execution' }
    let run1 = {
        status: 'pending'
    }
    let run2 = {
        status: 'successful',
        started_at: '2020-10-31T23:40:00+0000',
        finished_at: '2020-10-31T23:40:05+0000',
    }

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
        it('loads a single job', async () => {
            fetchMock.get('path:/api/job/job-1', job)
            let commit = jest.fn()
            await store.actions.load_job({ commit }, 'job-1')
            expect(commit).toHaveBeenCalledWith('current_job', job)
            expect(commit).toHaveBeenCalledWith('current_job_id', 'job-1')
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

    describe('load_runs', () => {
        let commit

        beforeEach(async () => {
            commit = jest.fn()
            fetchMock.get('path:/api/runs', { 'run-1': run1, 'run-2': run2 })
            fetchMock.get('path:/api/jobs', { 'job-1': job })
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

        it('calculates duration for completed jobs', () => {
            let runs = commit.mock.calls[0][1]
            expect(runs['run-2']).toHaveProperty('duration', '1m')
        })
    })
})