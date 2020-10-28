import fetchMock from 'fetch-mock-jest'
import store from '@/store.js'

describe('action current_job', () => {
    let job = { name: 'ze-name', execution: 'ze-execution' }
    let evaluation = { payload: { some: 'payload' } }

    beforeEach(() => fetchMock.mockReset())

    it('commits the new job and the evaluated evaluation', async () => {
        fetchMock.post('path:/api/jobs/evaluate', evaluation)
        let commit = jest.fn()
        await store.actions.current_job({ commit }, job)
        expect(commit).toHaveBeenCalledWith('current_job', { job, evaluation })
    })
})