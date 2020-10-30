const MockRouterLink = {
    name: 'router-link',
    props: ['to', 'class'],
    template: '{{this.to}} <slot/>',
}

export function mount_options(state) {
    let $store = {
        state: state,
        dispatch: jest.fn()
    }
    let options = {
        global: {
            components: { 'router-link': MockRouterLink },
            mocks: { $store }
        }
    }
    return { options, $store }

}
