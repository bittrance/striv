import { createRouter, createWebHashHistory } from 'vue-router'
import { createStore } from 'vuex'
import { createApp } from 'vue'
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css";

import App from './App.vue'
import CreateJob from './components/CreateJob.vue'
import Jobs from './components/Jobs.vue'
import PreviewPayload from '@/components/PreviewPayload.vue'
import store from '@/store.js'

const router = createRouter({
    history: createWebHashHistory(),
    routes: [
        { path: "/", component: Jobs },
        { path: "/jobs/new", component: CreateJob },
        { path: "/jobs/preview", component: PreviewPayload },
    ]
})

const app = createApp(App)
app.use(createStore(store))
app.use(router)
app.use(Toast)
app.mount('#app') 
