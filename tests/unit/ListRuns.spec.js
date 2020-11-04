import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ListRuns from '@/components/ListRuns.vue'

describe('ListRuns', () => {
    let options, $store
    let jobs = {
        'job-1': { name: 'job-1', execution: 'ze-execution' },
        'job-2': { name: 'job-2', execution: 'ze-execution' },
    }
    let runs = {
        'run-1': { job_id: 'job-1', created_at: '' },
        'run-2': { job_id: 'job-2', created_at: '' },
    }

    beforeEach(() => ({ options, $store } = mount_options({ jobs, runs })))

    it('asks store to load jobs and runs', () => {
        mount(ListRuns, options)
        expect($store.dispatch).toHaveBeenCalledWith('load_jobs')
        expect($store.dispatch).toHaveBeenCalledWith('load_runs')
    })

    it('lists runs in descending chronology', () => {
        let wrapper = mount(ListRuns, options)
        expect(wrapper.text()).toContain('job-1')
        expect(wrapper.text()).toContain('job-2')
    })
})
