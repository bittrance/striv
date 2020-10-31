import fetchMock from 'fetch-mock-jest'
import store from '@/store.js'

describe('actions', () => {
    let job = { name: 'ze-name', execution: 'ze-execution' }
    let evaluation = { payload: { some: 'payload' } }

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

    describe('store_current_job', () => {
        it('persists the current job', async () => {
            fetchMock.post('path:/api/jobs', job)
            await store.actions.store_current_job({ state: { current_job: job } })
            expect(fetchMock).toHaveFetched((url, req) => {
                expect(JSON.parse(req.body)).toHaveProperty('name', 'ze-name')
                return true
            })

        })
    })
})