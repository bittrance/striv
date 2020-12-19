import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ViewJob from '@/components/ViewJob.vue'

describe('ViewJob', () => {
    let options, $route, $router, $store
    let current_job = { name: 'Job 1', execution: 'ze-execution' }
    let jobs = { 'job-1': current_job }
    let runs = {
        'run-1': {
            job_id: 'job-1',
            status: 'pending',
            created_at: new Date('2020-10-31T23:40:00+0000')
        },
    }

    describe('before the store has data', () => {
        beforeEach(() => ({ options, $route, $store } = mount_options({ current_job: {}, jobs: {}, runs: {} })))
        beforeEach(() => $route.params.job_id = 'job-1')

        it('asks store to load the job', () => {
            mount(ViewJob, options)
            expect($store.dispatch).toHaveBeenCalledWith('load_jobs')
        })

        it('asks store to load the jobs runs', () => {
            mount(ViewJob, options)
            expect($store.dispatch).toHaveBeenCalledWith(
                'load_job_runs',
                expect.objectContaining({ job_id: 'job-1', newest: undefined })
            )
        })

        describe('when an older runs page is requested', () => {
            beforeEach(() => $route.query.newest = '2020-10-31T23:40:00Z')

            it('asks the store for older runs', () => {
                mount(ViewJob, options)
                expect($store.dispatch).toHaveBeenCalledWith(
                    'load_job_runs',
                    expect.objectContaining({ job_id: 'job-1', newest: expect.any(Date) })
                )
            })
        })
    })

    describe('once the store has received data', () => {
        beforeEach(() => {
            ({ options, $route, $router, $store } = mount_options({ current_job, jobs, runs }))
            $route.params.job_id = 'job-1'
            $store.dispatch.mockReturnValue(Promise.resolve())
        })

        it('displays the name', () => {
            let wrapper = mount(ViewJob, options)
            expect(wrapper.text()).toContain('Job 1')
        })

        it('provide a link to the view of each run for this job', () => {
            let wrapper = mount(ViewJob, options)
            expect(wrapper.text()).toContain('/run/run-1')
        })

        describe('when the delete button is pressed', () => {
            let wrapper
            beforeEach(async () => {
                wrapper = mount(ViewJob, options)
                await wrapper.find('[name="delete-job"]').trigger('click')
            })

            it('nothing happens', async () => {
                expect($store.dispatch).not.toHaveBeenCalledWith('delete_job')
            })

            describe('and then pressed again', () => {
                beforeEach(async () => await wrapper.find('[name="delete-job"]').trigger('click'))

                it('deletes the job', async () => {
                    expect($store.dispatch).toHaveBeenCalledWith('delete_job', 'job-1')
                })

                it('navigates back whence we came', () => {
                    expect($router.back).toHaveBeenCalled()
                })
            })
        })

        describe('when the run-job-now button is pressed', () => {
            it('invokes the store to run the job', async () => {
                let wrapper = mount(ViewJob, options)
                wrapper.find('[name="run-job-now"]').trigger('click')
                await wrapper.vm.$nextTick()
                expect($store.dispatch).toHaveBeenCalledWith('run_job_now', 'job-1')
            })
        })
    })
})