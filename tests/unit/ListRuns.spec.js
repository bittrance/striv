import { mount, shallowMount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ListRuns from '@/components/ListRuns.vue'

describe('ListRuns', () => {
    let options, $route, $router, $store
    let jobs = {
        'job-1': { name: 'job-1', execution: 'ze-execution' },
        'job-2': { name: 'job-2', execution: 'ze-execution' },
    }
    let runs = {
        'run-1': { job_id: 'job-1', created_at: new Date('2020-10-31T23:40:00+0000') },
        'run-2': { job_id: 'job-2', created_at: new Date('2020-10-31T23:41:00+0000') },
    }

    beforeEach(() => ({ options, $route, $store } = mount_options({ jobs, runs })))

    it('asks store to load jobs and runs', () => {
        mount(ListRuns, options)
        expect($store.dispatch).toHaveBeenCalledWith('load_jobs')
        expect($store.dispatch).toHaveBeenCalledWith('load_runs')
    })

    it('uses newest hash param when requesting runs', () => {
        $route.query['newest'] = '2020-10-31T23:40:00+0000'
        mount(ListRuns, options)
        expect($store.dispatch).toHaveBeenCalledWith('load_runs', expect.any(Date))
    })

    it('lists runs in descending chronology', () => {
        let wrapper = mount(ListRuns, options)
        expect(wrapper.text()).toContain('job-1')
        expect(wrapper.text()).toContain('job-2')
    })

    it('contains navigation to older runs', async () => {
        let wrapper = mount(ListRuns, options)
        expect(wrapper.text()).toContain('/runs?newest=2020-10-31T23:40:00')
    })
})
