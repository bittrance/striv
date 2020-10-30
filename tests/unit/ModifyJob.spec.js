import fetchMock from 'fetch-mock-jest'
import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import ModifyJob from '@/components/ModifyJob.vue'

describe('ModifyJob', () => {
    let { options, $store } = mount_options({
        dimensions: {},
        executions: { 'ze-execution': {} },
        current_job: {},
    })

    beforeEach(() => $store.dispatch.mockReset())
    beforeEach(() => fetchMock.mockReset())

    it('requests state on mounting', async () => {
        let wrapper = mount(ModifyJob, options)
        await wrapper.vm.$nextTick()
        expect($store.dispatch).toHaveBeenCalledWith('load_state')
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

    it('creates job on submit', async () => {
        fetchMock.post('path:/api/jobs', { id: 'ze-id' })
        let wrapper = mount(ModifyJob, options)
        await wrapper.find('#name').setValue('ze-name')
        await wrapper.find('form').trigger('submit')
        expect(fetchMock).toHaveFetched((url, req) => {
            expect(url).toBe('/api/jobs')
            expect(req.method).toBe('POST')
            expect(JSON.parse(req.body)).toHaveProperty('name', 'ze-name')
            return true
        })
    })
})