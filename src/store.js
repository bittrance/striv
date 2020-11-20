import { createToastInterface } from "vue-toastification";

const JOB_DATE_FIELDS = ['modified_at']
const RUN_DATE_FIELDS = ['created_at', 'started_at', 'finished_at']
const TOAST_OPTIONS = { timeout: 3000 }

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

async function load_runs(commit, state, base_url, newest) {
    let url = `${base_url}?limit=20`
    if (newest) {
        url += `&upper=${encodeURIComponent(newest.toISOString())}`
    }
    try {
        const response = await fetch(url)
        if (response.ok) {
            const runs = await response.json()
            for (const run of Object.values(runs)) {
                iso_string_to_date(run, RUN_DATE_FIELDS)
                if (run.started_at && run.finished_at) {
                    run.duration = duration(run)
                }
            }
            commit('load_runs', runs)
        } else {
            const message = await response.text()
            state.toast.error(message, TOAST_OPTIONS)
        }
    } catch (error) {
        state.toast.error(error, TOAST_OPTIONS)
    }
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
            current_run: {},
            current_run_logs: {},
            toast: createToastInterface(),
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
        current_run(state, run) {
            state.current_run = run
        },
        current_run_logs(state, logs) {
            state.current_run_logs = logs
        },
    },
    actions: {
        async load_state({ commit, state }) {
            try {
                const response = await fetch('/state')
                if (response.ok) {
                    const state = await response.json()
                    commit('load_state', state)
                } else {
                    const message = await response.text()
                    state.toast.error(message, TOAST_OPTIONS)
                }
            } catch (error) {
                state.toast.error(error, TOAST_OPTIONS)
            }
        },
        async current_job({ commit, state }, job) {
            commit('current_job', job)
            try {
                let response = await fetch("/jobs/evaluate", {
                    method: "POST",
                    headers: { "Content-type": "application/json" },
                    body: JSON.stringify(job),
                })
                if (response.status < 500) {
                    let evaluation = await response.json();
                    commit('current_job_evaluation', evaluation)
                } else {
                    let message = await response.text();
                    state.toast.error(message, TOAST_OPTIONS)
                }
            } catch (error) {
                state.toast.error(error, TOAST_OPTIONS)
            }
        },
        async load_job({ commit, state }, job_id) {
            try {
                const response = await fetch(`/job/${job_id}`)
                if (response.ok) {
                    const job = await response.json()
                    iso_string_to_date(job, JOB_DATE_FIELDS)
                    commit('current_job', job)
                    commit('current_job_id', job_id)
                } else {
                    const message = await response.text()
                    state.toast.error(message, TOAST_OPTIONS)
                }
            } catch (error) {
                state.toast.error(error, TOAST_OPTIONS)
            }
        },
        async load_job_runs({ commit, state }, { job_id, newest }) {
            await load_runs(commit, state, `/job/${job_id}/runs`, newest)
        },
        async load_jobs({ commit, state }) {
            try {
                const response = await fetch('/jobs')
                if (response.ok) {
                    const jobs = await response.json()
                    for (const job of Object.values(jobs)) {
                        iso_string_to_date(job, JOB_DATE_FIELDS)
                    }
                    commit('load_jobs', jobs)
                } else {
                    const message = await response.text()
                    state.toast.error(message, TOAST_OPTIONS)
                }
            } catch (error) {
                state.toast.error(error, TOAST_OPTIONS)
            }
        },
        async store_current_job({ state }) {
            let url, method
            if (state.current_job_id) {
                url = `/job/${state.current_job_id}`
                method = 'PUT'
            } else {
                url = '/jobs'
                method = 'POST'
            }
            return await fetch(url, {
                method: method,
                headers: { 'Content-type': 'application/json' },
                body: JSON.stringify(state.current_job),
            })
        },
        async load_runs({ commit, state }, newest) {
            await load_runs(commit, state, '/runs', newest)
        },
        async load_run({ commit, state }, run_id) {
            let run, job, logs
            try {
                [[run, job], logs] = await Promise.all([
                    fetch(`/run/${run_id}`)
                        .then(async (response) => {
                            if (response.ok) {
                                const run = await response.json()
                                response = await fetch(`/job/${run.job_id}`)
                                if (response.ok) {
                                    return [run, await response.json()]
                                } else {
                                    const message = await response.text()
                                    state.toast.error(message, TOAST_OPTIONS)
                                }
                            } else {
                                const message = await response.text()
                                state.toast.error(message, TOAST_OPTIONS)
                            }
                        }),
                    fetch(`/run/${run_id}/logs`)
                        .then(async (response) => {
                            if (response.ok) {
                                return await response.json()
                            } else {
                                const message = await response.text()
                                state.toast.error(message, TOAST_OPTIONS)
                            }
                        }),
                ])
            } catch (error) {
                state.toast.error(error, TOAST_OPTIONS)
                return
            }
            if (run != undefined && job != undefined && logs != undefined) {
                iso_string_to_date(run, RUN_DATE_FIELDS)
                if (run.started_at && run.finished_at) {
                    run.duration = duration(run)
                }
                commit('current_run', run)
                commit('current_run_logs', logs)
                commit('current_job', job)
                commit('current_job_id', run.job_id)
            }
        },
    }
}
