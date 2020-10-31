import { createRouter, createWebHashHistory } from 'vue-router'
import { createStore } from 'vuex'
import { createApp } from 'vue'
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css";

import App from './App.vue'
import ModifyJob from './components/ModifyJob.vue'
import ListJobs from './components/ListJobs.vue'
import PreviewPayload from '@/components/PreviewPayload.vue'
import store from '@/store.js'

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        { path: "/", component: ListJobs },
        { path: "/jobs/new", component: ModifyJob },
        { path: "/jobs/preview", component: PreviewPayload },
        { path: "/job/:job_id", component: ModifyJob },
    ]
})

const app = createApp(App)
app.use(createStore(store))
app.use(router)
app.use(Toast)
app.mount('#app') 
