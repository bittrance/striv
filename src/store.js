function iso_string_to_date(obj, props) {
    for (const prop of props) {
        if (obj[prop]) {
            obj[prop] = new Date(obj[prop])
        }
    }
}

function duration(run) {
    let delta = (run.finished_at - run.started_at) / 1000;
    let hours = Math.floor(delta / 3600);
    let minutes = Math.ceil((delta % 3600) / 60);
    let response = `${minutes}m`;
    if (hours > 0) {
        response = `${hours}h ${response}`;
    }
    return response;
}


export default {
    strict: true,
    state() {
        return {
            dimensions: {},
            executions: {},
            jobs: {},
            current_job: {},
            current_job_id: null,
            current_job_evaluation: null,
            runs: {},
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
        current_job_id(state, job_id) {
            state.current_job_id = job_id
        },
        current_job_evaluation(state, evaluation) {
            state.current_job_evaluation = evaluation
        },
        load_runs(state, runs) {
            state.runs = runs
        },
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
        async load_job({ commit }, job_id) {
            const response = await fetch(`/api/job/${job_id}`)
            let job = await response.json()
            iso_string_to_date(job, ['modified_at'])
            commit('current_job', job)
            commit('current_job_id', job_id)
        },
        async load_jobs({ commit }) {
            const response = await fetch('/api/jobs')
            const jobs = await response.json()
            for (const job of Object.values(jobs)) {
                iso_string_to_date(job, ['modified_at'])
            }
            commit('load_jobs', jobs)
        },
        async store_current_job({ state }) {
            let url, method
            if (state.current_job_id) {
                url = `/api/job/${state.current_job_id}`
                method = 'PUT'
            } else {
                url = `/api/jobs`
                method = 'POST'
            }
            return await fetch(url, {
                method: method,
                headers: { "Content-type": "application/json" },
                body: JSON.stringify(state.current_job),
            });
        },
        async load_runs({ commit }, newest) {
            let url = '/api/runs?limit=20'
            if (newest) {
                url += `&upper=${encodeURIComponent(newest.toISOString())}`
            }
            const response = await fetch(url)
            const runs = await response.json()
            for (const run of Object.values(runs)) {
                iso_string_to_date(run, ['created_at', 'started_at', 'finished_at'])
                if (run.started_at && run.finished_at) {
                    run.duration = duration(run)
                }
            }
            commit('load_runs', runs)
        }
    }
}
