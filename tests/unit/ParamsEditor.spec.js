import { mount } from '@vue/test-utils'
import ParamsEditor from '@/components/ParamsEditor.vue'

describe('ParamsEditor', () => {
    let params = { param1: 'value1', param2: 'value2' }

    let wrapper
    beforeEach(() => wrapper = mount(ParamsEditor, { props: { params } }))

    test('presents existing parameters', () => {
        expect(wrapper.text()).toContain('param1')
        expect(wrapper.text()).toContain('param2')
        expect(wrapper.text()).toContain('value1')
        expect(wrapper.text()).toContain('value2')
    })

    describe('when set readonly', () => {
        it('does not contain input controls', () => {
            let wrapper = mount(ParamsEditor, { props: { params, readonly: true } })
            expect(wrapper.find("input").exists()).toBeFalsy()
        })

        describe('and there are no params', () => {
            it('provides a placeholder', () => {
                let wrapper = mount(ParamsEditor, { props: { params: {}, readonly: true } })
                expect(wrapper.text()).toContain("No parameters")
            })
        })
    })

    describe('when an add button is pressed', () => {
        test('does not emit add-param without input values', async () => {
            wrapper.find('[name="add-param"]').trigger('click')
            await wrapper.vm.$nextTick()
            expect(wrapper.emitted()).toStrictEqual({})
        })

        describe('with input values', () => {
            test('emits add-param events', async () => {
                wrapper.find('[name="param-name"]').setValue('param3')
                wrapper.find('[name="param-value"]').setValue('value3')
                wrapper.find('[name="add-param"]').trigger('click')
                await wrapper.vm.$nextTick()
                expect(wrapper.emitted()).toStrictEqual({ 'add-param': [['param3', 'value3']] })
            })
        })
    })

    describe('when a delete button is pressed', () => {
        beforeEach(async () => {
            wrapper.find('[name="delete-param"]').trigger('click')
            await wrapper.vm.$nextTick()
        })

        test('emits delete-param event', () => {
            expect(wrapper.emitted()).toStrictEqual({ 'delete-param': [['param1']] })
        })

        test('puts the parameter back for easy adding', () => {
            expect(wrapper.find('[name="param-name"]').element.value).toBe('param1')
            expect(wrapper.find('[name="param-value"]').element.value).toBe('value1')
        })
    })
})
