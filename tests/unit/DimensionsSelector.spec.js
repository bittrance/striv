import { mount } from '@vue/test-utils'
import DimensionsSelector from '@/components/DimensionsSelector.vue'

describe('DimensionsSelector', () => {
    let available = {
        dim1: { values: { dim1val1: {}, dim1val2: {}, } },
        dim2: { values: { dim2val1: {} } },
        dim3: { values: { dim3val1: {} } }
    }
    let selected = { dim3: 'dim3val1' }
    let options = { props: { available, selected } }

    let wrapper
    beforeEach(() => wrapper = mount(DimensionsSelector, options))

    it('lists dimensions for selection', () => {
        expect(wrapper.text()).toContain('dim1')
        expect(wrapper.text()).toContain('dim2')
        expect(wrapper.text()).not.toContain('dim1val1')
    })

    it('allows selecting from selected dimensions values', async () => {
        await wrapper.find('[name="new-name"]').setValue('dim1')
        expect(wrapper.text()).toContain('dim1val1')
        expect(wrapper.text()).toContain('dim1val2')
        expect(wrapper.text()).not.toContain('dim2val1')
    })

    describe('when set readonly', () => {
        it('does not contain input controls', () => {
            let options = { props: { available, selected, readonly: true } }
            let wrapper = mount(DimensionsSelector, options)
            expect(wrapper.find("select").exists()).toBeFalsy()
        })

        describe('and there are no dimensions', () => {
            it('provides a placeholder', () => {
                let options = { props: { available: {}, selected: {}, readonly: true } }
                let wrapper = mount(DimensionsSelector, options)
                expect(wrapper.text()).toContain("No dimensions")
            })
        })
    })

    describe('with selected dimeinsions', () => {
        it('lists selected dimensions', () => {
            expect(wrapper.text()).toContain('dim3val1')
        })
    })

    describe('when an add button is pressed', () => {
        it('does not emit add-diemsion without no values', async () => {
            await wrapper.find('[name="add-dimension"]').trigger('click')
            expect(wrapper.emitted()).toStrictEqual({})
        })

        it('does not emit add-diemsion with only name', async () => {
            await wrapper.find('[name="new-name"]').setValue('dim1')
            await wrapper.find('[name="add-dimension"]').trigger('click')
            expect(wrapper.emitted()).toStrictEqual({})
        })

        it('emits add-dimension events with name and value selected', async () => {
            await wrapper.find('[name="new-name"]').setValue('dim1')
            await wrapper.find('[name="new-value"]').setValue('dim1val1')
            await wrapper.find('[name="add-dimension"]').trigger('click')
            expect(wrapper.emitted()).toStrictEqual({ 'add-dimension': [['dim1', 'dim1val1']] })
        })
    })

    describe('when a delete button is pressed', () => {
        beforeEach(async () => {
            await wrapper.find('[name="delete-dimension"]').trigger('click')
        })

        it('emits delete-dimension event', () => {
            expect(wrapper.emitted()).toStrictEqual({ 'delete-dimension': [['dim3']] })
        })

        it('selects the dimension for easy re-adding', () => {
            expect(wrapper.find('[name="new-name"]').element.value).toBe('dim3')
            expect(wrapper.find('[name="new-value"]').element.value).toBe('dim3val1')
        })
    })
})
