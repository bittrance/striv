import { mount, shallowMount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ListRuns from '@/components/ListRuns.vue'

describe('ListRuns', () => {
    let options, $route, $store
    let jobs = {}
    let runs = {}

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
})
