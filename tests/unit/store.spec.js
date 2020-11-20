import fetchMock from 'fetch-mock-jest'
import store from '@/store.js'

fetchMock.config.overwriteRoutes = true

describe('actions', () => {
    let evaluation = { payload: { some: 'payload' } }
    let job = {
        name: 'ze-name',
        execution: 'ze-execution',
        modified_at: '2020-10-31T23:40:00+0000'
    }
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

    let state = { toast: { error: jest.fn() } }
    let commit = jest.fn()

    beforeEach(() => {
        fetchMock.mockReset()
        state.toast.error.mockReset()
        commit.mockReset()
    })

    describe('load_state', () => {
        it('returns the state', async () => {
            fetchMock.get('path:/state', { some: 'state' })
            await store.actions.load_state({ commit, state })
            expect(commit).toHaveBeenCalledWith('load_state', { some: 'state' })
            expect(state.toast.error).not.toHaveBeenCalled()
        })

        describe('when fetch errors', () => {
            it('does not commit the state', async () => {
                fetchMock.get('path:/state', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_state({ commit, state })
                expect(state.toast.error).toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/state', { throws: new Error('boom!') })
                await store.actions.load_state({ commit, state })
                expect(state.toast.error).toHaveBeenCalled()
            })
        })
    })

    describe('current_job', () => {
        it('commits the new job and the evaluated evaluation', async () => {
            fetchMock.post('path:/jobs/evaluate', evaluation)
            await store.actions.current_job({ commit, state }, job)
            expect(commit).toHaveBeenCalledWith('current_job', job)
            expect(commit).toHaveBeenCalledWith('current_job_evaluation', evaluation)
            expect(state.toast.error).not.toHaveBeenCalled()
        })

        describe('when the evaluation is found invalid', () => {
            let failure = { invalid: true }

            it('commits the new job and the evaluated evaluation', async () => {
                fetchMock.post('path:/jobs/evaluate', { status: 400, body: failure })
                await store.actions.current_job({ commit, state }, job)
                expect(commit).toHaveBeenCalledWith('current_job', job)
                expect(commit).toHaveBeenCalledWith('current_job_evaluation', failure)
                expect(state.toast.error).not.toHaveBeenCalled()
            })
        })

        describe('when the evaluation breaks', () => {
            it('does not commit on server-side failure', async () => {
                fetchMock.post('path:/jobs/evaluate', { status: 500, body: { bad: 'ness' } })
                await store.actions.current_job({ commit, state }, job)
                expect(commit).toHaveBeenCalledWith('current_job', job)
                expect(commit).not.toHaveBeenCalledWith('current_job_evaluation', expect.anything())
            })

            it('toasts the error', async () => {
                fetchMock.post('path:/jobs/evaluate', { status: 500, body: { bad: 'ness' } })
                await store.actions.current_job({ commit, state }, job)
                expect(state.toast.error).toHaveBeenCalled()
            })
        })

        describe('when fetch errors', () => {
            it('does not commit on client-side failure', async () => {
                fetchMock.post('path:/jobs/evaluate', { throws: new Error('boom!') })
                await store.actions.current_job({ commit, state }, job)
                expect(commit).toHaveBeenCalledWith('current_job', job)
                expect(commit).not.toHaveBeenCalledWith('current_job_evaluation', expect.anything())
            })

            it('toasts the error', async () => {
                fetchMock.post('path:/jobs/evaluate', { throws: new Error('boom!') })
                await store.actions.current_job({ commit, state }, job)
                expect(state.toast.error).toHaveBeenCalled()
            })
        })
    })

    describe('load_job', () => {
        it('loads a single job', async () => {
            fetchMock.get('path:/job/job-1', job)
            await store.actions.load_job({ commit, state }, 'job-1')
            expect(commit).toHaveBeenCalledWith(
                'current_job',
                expect.objectContaining({ name: 'ze-name' })
            )
            expect(commit).toHaveBeenCalledWith('current_job_id', 'job-1')
        })

        it('converts ISO date strings to date objects', async () => {
            fetchMock.get('path:/job/job-1', job)
            await store.actions.load_job({ commit, state }, 'job-1')
            expect(commit).toHaveBeenCalledWith(
                'current_job',
                expect.objectContaining({ modified_at: expect.any(Date) })
            )
        })

        describe('when backend errors', () => {
            it('does not commit jobs', async () => {
                fetchMock.get('path:/job/job-1', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_job({ commit, state }, 'job-1')
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/job/job-1', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_job({ commit, state }, 'job-1')
                expect(state.toast.error).toHaveBeenCalled()
            })
        })

        describe('when fetch errors', () => {
            it('does not commit jobs', async () => {
                fetchMock.get('path:/job/job-1', { throws: new Error('boom!') })
                await store.actions.load_job({ commit, state }, 'job-1')
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/job/job-1', { throws: new Error('boom!') })
                await store.actions.load_job({ commit, state }, 'job-1')
                expect(state.toast.error).toHaveBeenCalled()
            })
        })
    })

    describe('load_jobs', () => {
        it('loads a single job', async () => {
            fetchMock.get('path:/jobs', { 'job-1': job })
            await store.actions.load_jobs({ commit, state })
            expect(commit).toHaveBeenCalledWith(
                'load_jobs',
                expect.objectContaining({
                    'job-1': expect.objectContaining({ modified_at: expect.any(Date) })
                })
            )
        })

        describe('when backend errors', () => {
            it('does not commit jobs', async () => {
                fetchMock.get('path:/jobs', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_jobs({ commit, state })
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/jobs', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_jobs({ commit, state })
                expect(state.toast.error).toHaveBeenCalled()
            })
        })

        describe('when fetch errors', () => {
            it('does not commit jobs', async () => {
                fetchMock.get('path:/jobs', { throws: new Error('boom!') })
                await store.actions.load_jobs({ commit, state })
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/jobs', { throws: new Error('boom!') })
                await store.actions.load_jobs({ commit, state })
                expect(state.toast.error).toHaveBeenCalled()
            })
        })
    })

    describe('store_current_job', () => {
        beforeEach(() => state.current_job = job)

        it('persists the current job as a new job', async () => {
            fetchMock.post('path:/jobs', job)
            await store.actions.store_current_job({ commit, state })
            expect(fetchMock).toHaveFetched((url, req) => {
                expect(JSON.parse(req.body)).toHaveProperty('name', 'ze-name')
                return true
            })
        })

        describe('when current job id is known', () => {
            beforeEach(() => {
                state.current_job = job
                state.current_job_id = 'job-1'
            })

            it('updates the existing job', async () => {
                fetchMock.put('path:/job/job-1', '')
                await store.actions.store_current_job({ state })
                expect(fetchMock).toHaveFetched()
            })
        })
    })

    describe('load_runs and load_job_runs', () => {
        beforeEach(() => {
            fetchMock.get('path:/runs', { 'run-1': run1, 'run-2': run2 })
        })

        it('loads the runs', async () => {
            await store.actions.load_runs({ commit, state })
            expect(commit).toHaveBeenCalledWith(
                'load_runs',
                expect.objectContaining({
                    'run-1': expect.anything(),
                    'run-2': expect.anything(),
                })
            )
        })

        it('converts ISO date strings to date objects', async () => {
            await store.actions.load_runs({ commit, state })
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

        it('calculates duration for completed jobs', async () => {
            await store.actions.load_runs({ commit, state })
            let runs = commit.mock.calls[0][1]
            expect(runs['run-2']).toHaveProperty('duration', '1m')
        })

        describe('when backend errors', () => {
            it('does not commit runs', async () => {
                fetchMock.get('path:/runs', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_runs({ commit, state })
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/runs', { status: 500, body: { bad: 'ness' } })
                await store.actions.load_runs({ commit, state })
                expect(state.toast.error).toHaveBeenCalled()
            })
        })

        describe('when fetch errors', () => {
            it('does not commit runs', async () => {
                fetchMock.get('path:/runs', { throws: new Error('boom!') })
                await store.actions.load_runs({ commit, state })
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get('path:/runs', { throws: new Error('boom!') })
                await store.actions.load_runs({ commit, state })
                expect(state.toast.error).toHaveBeenCalled()
            })
        })
    })

    describe('load_run', () => {
        beforeEach(async () => {
            fetchMock.get('path:/run/run-1', run1)
            fetchMock.get('path:/run/run-1/logs', logs1)
            fetchMock.get('path:/job/job-1', job)
        })

        it('commits the run and its logs', async () => {
            await store.actions.load_run({ commit, state }, 'run-1')
            expect(commit).toHaveBeenCalledWith(
                'current_run',
                expect.objectContaining({
                    status: 'pending',
                    created_at: expect.any(Date),
                })
            )
            expect(commit).toHaveBeenCalledWith('current_run_logs', logs1)
        })

        it('commits the runs job and job id', async () => {
            await store.actions.load_run({ commit, state }, 'run-1')
            expect(commit).toHaveBeenCalledWith(
                'current_job',
                expect.objectContaining({ name: 'ze-name' })
            )
            expect(commit).toHaveBeenCalledWith('current_job_id', 'job-1')
        })

        it('converts ISO date strings to date objects', async () => {
            await store.actions.load_run({ commit, state }, 'run-1')
            expect(commit).toHaveBeenCalledWith(
                'current_run',
                expect.objectContaining({ created_at: expect.any(Date) })
            )
        })

        describe.each([
            ['path:/run/run-1'],
            ['path:/run/run-1/logs'],
            ['path:/job/job-1'],
        ])(`when %s fails`, (endpoint) => {
            it('does not commit jobs', async () => {
                fetchMock.get(endpoint, { status: 500, body: { bad: 'ness' } })
                await store.actions.load_run({ commit, state }, 'run-1')
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get(endpoint, { status: 500, body: { bad: 'ness' } })
                await store.actions.load_run({ commit, state }, 'run-1')
                expect(state.toast.error).toHaveBeenCalled()
            })
        })

        describe.each([
            ['path:/run/run-1'],
            ['path:/run/run-1/logs'],
            ['path:/job/job-1'],
        ])(`when client errors on %s`, (endpoint) => {
            it('does not commit jobs', async () => {
                fetchMock.get(endpoint, { throws: new Error('boom!') })
                await store.actions.load_run({ commit, state }, 'run-1')
                expect(commit).not.toHaveBeenCalled()
            })

            it('toasts the error', async () => {
                fetchMock.get(endpoint, { throws: new Error('boom!') })
                await store.actions.load_run({ commit, state }, 'run-1')
                expect(state.toast.error).toHaveBeenCalled()
            })
        })
    })
})