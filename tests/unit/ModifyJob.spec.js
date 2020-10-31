import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ModifyJob from '@/components/ModifyJob.vue'

describe('ModifyJob', () => {
    let options, $route, $router, $store

    beforeEach(() => ({ options, $route, $router, $store } = mount_options({
        dimensions: {},
        executions: { 'ze-execution': {} },
        current_job: {},
    })))

    it('requests state on mounting', async () => {
        let wrapper = mount(ModifyJob, options)
        await wrapper.vm.$nextTick()
        expect($store.dispatch).toHaveBeenCalledWith('load_state')
    })

    it('requests the store to unset the job id (i.e. enter create mode)', () => {
        mount(ModifyJob, options)
        expect($store.commit).toHaveBeenCalledWith('current_job_id', undefined)
    })

    it('has a create button in create mode', () => {
        let wrapper = mount(ModifyJob, options)
        let button = wrapper.find('[type="submit"]')
        expect(button.element.value).toEqual('Create')
    })

    it('updates the store when execution changes', async () => {
        let wrapper = mount(ModifyJob, options)
        await wrapper.find('#execution').setValue('ze-execution')
        expect($store.dispatch).toHaveBeenCalledWith(
            'current_job',
            expect.objectContaining({ execution: 'ze-execution' })
        )
    })

    it('updates the store when params change', async () => {
        let wrapper = mount(ModifyJob, options)
        wrapper.findComponent({ name: 'ParamsEditor' })
            .vm.$emit('add-param', 'this', 'that')
        await wrapper.vm.$nextTick()
        expect($store.dispatch).toHaveBeenCalledWith(
            'current_job',
            expect.objectContaining({ params: { this: 'that' } })
        )
    })

    describe('when invoked with an existing job', () => {
        beforeEach(() => {
            $route.params.job_id = 'job-1'
            $store.state.current_job_id = 'job-1'
        })

        it('requests the store to load the job', () => {
            let wrapper = mount(ModifyJob, options)
            expect($store.dispatch).toHaveBeenCalledWith('load_job', 'job-1')
        })

        it('has a modify button', () => {
            let wrapper = mount(ModifyJob, options)
            let button = wrapper.find('[type="submit"]')
            expect(button.element.value).toEqual('Modify')
        })
    })

    describe('on submit', () => {
        let wrapper
        let response = Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 'ze-id' }) })

        beforeEach(async () => {
            $store.dispatch.mockReturnValue(response)
            let wrapper = mount(ModifyJob, options)
            await wrapper.find('#name').setValue('ze-name')
            await wrapper.find('form').trigger('submit')
        })

        it('asks the store to create the job on submit', async () => {
            expect($store.dispatch).toHaveBeenCalledWith('store_current_job')
        })

        it('routes back to jobs list', () => {
            expect($router.push).toHaveBeenCalled()
        })
    })
})