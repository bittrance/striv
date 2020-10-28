import { mount } from '@vue/test-utils'
import PreviewPayload from '@/components/PreviewPayload.vue'

const MockRouterLink = {
    name: 'router-link',
    props: ['to', 'class'],
    template: 'hello',
}

describe('PreviewPayload', () => {
    let evaluation = { payload: { some: 'ze-payload' } }
    let $store = {
        state: {
            current_job_evaluation: evaluation
        },
        dispatch: jest.fn()
    }
    let options = {
        global: {
            components: { 'router-link': MockRouterLink },
            mocks: { $store }
        }
    }

    it('displays evaluated payload', async () => {
        let wrapper = mount(PreviewPayload, options)
        expect(wrapper.text()).toContain('ze-payload')
        expect($store.dispatch).toHaveBeenCalled()
    })
})