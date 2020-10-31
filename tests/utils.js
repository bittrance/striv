const MockRouterLink = {
    name: 'router-link',
    props: ['to', 'class'],
    template: '{{this.to}} <slot/>',
}

export function mount_options(state) {
    let $route = { params: {} }
    let $router = { push: jest.fn() }
    let $store = {
        state: state,
        dispatch: jest.fn()
    }
    let options = {
        global: {
            components: { 'router-link': MockRouterLink },
            mocks: { $route, $router, $store }
        }
    }
    return { options, $route, $router, $store }

}
