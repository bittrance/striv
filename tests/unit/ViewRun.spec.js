import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ViewRun from '@/components/ViewRun.vue'

describe('ViewRun', () => {
    let options, $route, $store
    let current_job = { name: 'job-1', execution: 'ze-execution' }
    let current_run = {
        job_id: 'job-1',
        status: 'pending',
        created_at: new Date('2020-10-31T23:40:00+0000')
    }
    let current_run_logs = {
        'task1/stdout': 'ze-out',
        'task1/stderr': 'ze-err',
    }

    beforeEach(() => {
        ({ options, $route, $store } = mount_options({
            current_run: {},
            current_run_logs: {},
            current_job: {},
        }))
        $route.params.run_id = 'run-1'
    })

    it('asks store to load jobs and runs', () => {
        mount(ViewRun, options)
        expect($store.dispatch).toHaveBeenCalledWith('load_run', 'run-1')
    })

    describe('with run data loaded', () => {
        beforeEach(() => {
            ({ options, $route, $store } = mount_options({
                current_run,
                current_run_logs,
                current_job,
            }))
            $route.params.run_id = 'run-1'
        })

        it('renders an edit link for the job', () => {
            let wrapper = mount(ViewRun, options)
            expect(wrapper.text()).toContain('/job/job-1')
        })

        it('renders an expandable section for each log', () => {
            let wrapper = mount(ViewRun, options)
            expect(wrapper.text()).toContain('?expand=task1%2Fstdout')
            expect(wrapper.text()).toContain('?expand=task1%2Fstderr')
        })

        it('renders logs in compact format', () => {
            let wrapper = mount(ViewRun, options)
            expect(wrapper.findAll('.log-container').length).toEqual(2)
        })

        describe('given a log to expand', () => {
            beforeEach(() => $route.query.expand = 'task1/stdout')

            it('it does not render that log expanded', () => {
                let wrapper = mount(ViewRun, options)
                expect(wrapper.findAll('.log-container').length).toEqual(1)
            })
        })
    })
})