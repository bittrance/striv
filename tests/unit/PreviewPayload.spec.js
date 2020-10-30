import { mount } from '@vue/test-utils'
import { mount_options } from '../utils'
import PreviewPayload from '@/components/PreviewPayload.vue'

describe('PreviewPayload', () => {
    let state = { current_job_evaluation: { payload: { some: 'ze-payload' } } }

    it('displays evaluated payload', async () => {
        let { options, $store } = mount_options(state)
        let wrapper = mount(PreviewPayload, options)
        expect(wrapper.text()).toContain('ze-payload')
        expect($store.dispatch).toHaveBeenCalled()
    })
})