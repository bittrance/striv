import { mount } from '@vue/test-utils'
import ParamsEditor from '@/components/ParamsEditor.vue'

describe('ParamsEditor', () => {
    const params = {
        param1: 'value1',
        param2: { type: 'secret', encrypted: 'encrypted' }
    }
    const public_key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAts0tCjEj+FLJrwzFaFgoeQEAZ8/tWaH2pWM5sisaxmVH/2c32fgMVBQbs5hrr/EpwHLCR+S8W3s908Ne91L+n9QCEJCesDGJRljHrINYxqa8ilhzgQIH33cMvqtvrOWh43bPQUbHVSzNY6/TTsYX9Qn6h5EwV3j02MkgFGF/4yRHuqsMNMTO8o554xzqaoVgV2EAk+GREMtt07RlUXOg e2Ty3VXiJOfHWE7kUYgFhSBtm7AQK3KOHKVsACHBi6z+nIF2uDBeBr26AP5kMab7uQp6M2h/e2VVWwr743UsZoyXEsEchYzBR6RdE32pDVmR84oOlzILj0XcYDCjH/Xq/wIDAQAB'

    let wrapper
    beforeEach(() => wrapper = mount(ParamsEditor, { props: { params } }))

    it('presents the existing parameter', () => {
        expect(wrapper.text()).toContain('param1')
        expect(wrapper.text()).toContain('value1')
    })

    it('redacts the secret', () => {
        expect(wrapper.text()).toContain('param2')
        expect(wrapper.text()).toContain('<redacted>')
        expect(wrapper.text()).not.toContain('encrypted')
    })

    it('does not allow creating secrets', () => {
        let type = wrapper.find('[id="param-type-secret"]')
        expect(type.element.disabled).toBe(true)
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

    describe('when a public key is available', () => {
        beforeEach(() => wrapper = mount(ParamsEditor, { props: { params, public_key } }))

        it('allows creating secrets', () => {
            let type = wrapper.find('[id="param-type-secret"]')
            expect(type.element.disabled).toBe(false)
        })

        describe('and the add button is pressed with a secret', () => {
            /* TypeError: Cannot read property 'activeElement' of null from webcrypto.encrypt */
            it.skip('emits an add-param event with a value object', async () => {
                wrapper.find('[name="param-name"]').setValue('param3')
                wrapper.find('[name="param-type"]').setValue('secret')
                wrapper.find('[name="param-value"]').setValue('verrah-secret')
                wrapper.find('[name="add-param"]').trigger('click')
                await wrapper.vm.$nextTick()
                expect(wrapper.emitted()).toStrictEqual({
                    'add-param': [
                        ['param3', {
                            type: 'secret',
                            encrypted: expect.stringMatching('.{255}')
                        }]
                    ]
                })
            })
        })

        describe('and a secret is deleted', () => {
            beforeEach(async () => {
                const delete_buttons = wrapper.findAll('[name="delete-param"]')
                delete_buttons[delete_buttons.length - 1].trigger('click')
                await wrapper.vm.$nextTick()
            })

            it('emits delete-param event', () => {
                expect(wrapper.emitted()).toStrictEqual({ 'delete-param': [['param2']] })
            })

            it('does not put the parameter back for easy input', () => {
                expect(wrapper.find('[name="param-name"]').element.value).toBe('')
                expect(wrapper.find('[name="param-type"]').element.value).toBe('text')
                expect(wrapper.find('[name="param-value"]').element.value).toBe('')
            })
        })
    })
})
