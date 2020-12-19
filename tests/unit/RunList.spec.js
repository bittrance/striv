import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ListRuns from '@/components/ListRuns.vue'

describe('ListRuns', () => {
    let options, $route
    let jobs = {
        'job-1': { name: 'Job 1', execution: 'ze-execution' },
        'job-2': { name: 'Job 2', execution: 'ze-execution' },
    }
    let runs = {
        'run-1': { job_id: 'job-1', created_at: new Date('2020-10-31T23:40:00+0000') },
        'run-2': { job_id: 'job-2', created_at: new Date('2020-10-31T23:41:00+0000') },
    }

    beforeEach(() => ({ options, $route } = mount_options({ jobs, runs })))

    describe('once the store has received data', () => {
        it('lists runs in descending chronology', () => {
            let wrapper = mount(ListRuns, options)
            expect(wrapper.text()).toContain('Job 1')
            expect(wrapper.text()).toContain('Job 2')
        })

        it('navigates to current url', () => {
            $route.path = '/some/path'
            let wrapper = mount(ListRuns, options)
            expect(wrapper.text()).toContain('/some/path')
        })

        it('contains navigation to older runs', async () => {
            let wrapper = mount(ListRuns, options)
            expect(wrapper.text()).toContain('?newest=2020-10-31T23:40:00')
        })
    })

    describe('when a runs job has been deleted', () => {
        let jobs = {
            'job-2': { name: 'Job 2', execution: 'ze-execution' },
        }

        beforeEach(() => ({ options, $route } = mount_options({ jobs, runs })))

        it('it renders its name as deleted', () => {
            let wrapper = mount(ListRuns, options)
            expect(wrapper.text()).toContain('<deleted>')
        })
    })
})
