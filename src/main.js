import { createRouter, createWebHashHistory } from 'vue-router'
import { createStore } from 'vuex'
import { createApp } from 'vue'
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css";

import App from './App.vue'
import CreateJob from './components/CreateJob.vue'
import Jobs from './components/Jobs.vue'

const store = createStore({
    state() {
        return {
            dimensions: {},
            executions: {},
            jobs: {}
        }
    },
    mutations: {
        load_state(state, api_state) {
            state.dimensions = api_state.dimensions
            state.executions = api_state.executions
        },
        load_jobs(state, jobs) {
            state.jobs = jobs
        }
    },
    actions: {
        async load_state({ commit }) {
            const response = await fetch('/api/state')
            const state = await response.json()
            commit('load_state', state)
        },
        async load_jobs({ commit }) {
            const response = await fetch('/api/jobs')
            const jobs = await response.json()
            commit('load_jobs', jobs)
        }
    }
})

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        { path: "/", component: Jobs },
        { path: "/jobs/new", component: CreateJob },
    ]
})

const app = createApp(App)
app.use(store)
app.use(router)
app.use(Toast)
app.mount('#app') 
