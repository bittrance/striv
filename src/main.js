import { createRouter, createWebHashHistory } from 'vue-router'
import { createStore } from 'vuex'
import { createApp } from 'vue'
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css";

import App from './App.vue'
import ModifyJob from './components/ModifyJob.vue'
import ListJobs from './components/ListJobs.vue'
import ViewJob from './components/ViewJob.vue'
import ListRuns from './components/ListRuns.vue'
import ViewRun from './components/ViewRun.vue'
import PreviewPayload from '@/components/PreviewPayload.vue'
import store from '@/store.js'
import '@/striv.css'

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        { path: "/jobs", component: ListJobs },
        { path: "/jobs/new", component: ModifyJob },
        { path: "/jobs/preview", component: PreviewPayload },
        { path: "/job/:job_id", component: ViewJob },
        { path: "/job/:job_id/modify", component: ModifyJob },
        { path: "/runs", alias: "/", component: ListRuns },
        { path: "/run/:run_id", component: ViewRun },
    ]
})

const app = createApp(App)
app.use(createStore(store))
app.use(router)
app.use(Toast)
app.mount('#app') 
