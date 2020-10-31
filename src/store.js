export default {
    strict: true,
    state() {
        return {
            dimensions: {},
            executions: {},
            jobs: {},
            current_job: {},
            current_job_evaluation: null,
        }
    },
    mutations: {
        load_state(state, api_state) {
            state.dimensions = api_state.dimensions
            state.executions = api_state.executions
        },
        load_jobs(state, jobs) {
            state.jobs = jobs
        },
        current_job(state, job) {
            state.current_job = job
        },
        current_job_evaluation(state, evaluation) {
            state.current_job_evaluation = evaluation
        }
    },
    actions: {
        async load_state({ commit }) {
            const response = await fetch('/api/state')
            const state = await response.json()
            commit('load_state', state)
        },
        async current_job({ commit }, job) {
            commit('current_job', job)
            let response = await fetch("/api/jobs/evaluate", {
                method: "POST",
                headers: { "Content-type": "application/json" },
                body: JSON.stringify(job),
            })
            let evaluation = await response.json();
            commit('current_job_evaluation', evaluation)
        },
        async load_jobs({ commit }) {
            const response = await fetch('/api/jobs')
            const jobs = await response.json()
            commit('load_jobs', jobs)
        },
        async store_current_job({ state }) {
            return await fetch("/api/jobs", {
                method: "POST",
                headers: { "Content-type": "application/json" },
                body: JSON.stringify(state.current_job),
            });
        }
    }
}
