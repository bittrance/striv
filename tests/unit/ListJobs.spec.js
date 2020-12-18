import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ListJobs from '@/components/ListJobs.vue'

describe('ListJobs', () => {
    let options, $store
    let jobs = {
        '1': { name: 'job1', execution: 'ze-execution' },
        '2': { name: 'job2', execution: 'ze-execution' },
    }

    beforeEach(() => ({ options, $store } = mount_options({ jobs })))

    it('asks store to load jobs', () => {
        mount(ListJobs, options)
        expect($store.dispatch).toHaveBeenCalledWith('load_jobs', true)
    })

    it('lists jobs', () => {
        let wrapper = mount(ListJobs, options)
        expect(wrapper.text()).toContain('job1')
        expect(wrapper.text()).toContain('job2')
    })

    it('includes link to view jobs', () => {
        let wrapper = mount(ListJobs, options)
        wrapper.findAllComponents('router-link')
        expect(wrapper.text()).toContain('/job/1 ')
        expect(wrapper.text()).toContain('/job/2 ')
    })

    it('includes link to edit jobs', () => {
        let wrapper = mount(ListJobs, options)
        wrapper.findAllComponents('router-link')
        expect(wrapper.text()).toContain('/job/1/modify')
        expect(wrapper.text()).toContain('/job/2/modify')
    })
})