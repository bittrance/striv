import { createStore } from 'vuex'
import { createApp } from 'vue'
import App from './App.vue'

const store = createStore({
    state() {
        return {
            jobs: {}
        }
    },
    mutations: {
        load_jobs(state, jobs) {
            state.jobs = jobs
        }
    },
    actions: {
        async load_jobs({ commit }) {
            const response = await fetch('http://localhost:8081/jobs')
            const jobs = await response.json()
            commit('load_jobs', jobs)
        }
    }
})

const app = createApp(App)
app.use(store)
app.mount('#app') 
