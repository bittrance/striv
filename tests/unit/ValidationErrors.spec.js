import { mount } from '@vue/test-utils'
import ValidationErrors from '@/components/ValidationErrors.vue'

describe('ValidationErrors', () => {
    describe('given a field-level validation error', () => {
        let error = { title: 'invalid', 'invalid-fields': { 'field': ['error'] } }

        test('presents error title', () => {
            let wrapper = mount(ValidationErrors, { props: { error } })
            expect(wrapper.text()).toContain('invalid')
        })

        test('presents invalid fields', () => {
            let wrapper = mount(ValidationErrors, { props: { error } })
            expect(wrapper.text()).toContain('field')
            expect(wrapper.text()).toContain('error')
        })
    })

    describe('given a jsonnet validation error', () => {
        let error = { title: 'ze-failure', detail: 'badness', source: 'ze-template' }

        test('presents detail', () => {
            let wrapper = mount(ValidationErrors, { props: { error } })
            expect(wrapper.text()).toContain('badness')
        })
    })
})