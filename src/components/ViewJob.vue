<template>
  <div>
    <div class="float-right pt-3 px-3">
      <button
        type="button"
        name="run-job-now"
        title="Run job now"
        class="btn btn-lg text-primary fas fa-play fa-2x"
        @click="run_job_now"
      />
    </div>
    <div class="row px-3 py-3">
      <div class="col-sm">
        <small>Job name</small>
        <div>
          {{ job.name }}
          <router-link :to="`/job/${job_id}/modify`" class="btn text-primary"
            ><i class="fas fa-edit"></i
          ></router-link>
        </div>
      </div>
      <div class="col-sm">
        <small>Modified at</small>
        <div>{{ compactDateTime(job.modified_at) }}</div>
      </div>
      <div class="col-sm">
        <small>Execution</small>
        <div>{{ job.execution }}</div>
      </div>
    </div>
    <div class="row px-3 py-3">
      <div class="col-sm">
        <h2>Dimensions</h2>
        <dimensions-selector
          :available="{}"
          :selected="job.dimensions || {}"
          :readonly="true"
        />
      </div>
      <div class="col-sm">
        <h2>Job-specific parameters</h2>
        <params-editor :params="job.params || {}" :readonly="true" />
      </div>
    </div>
    <div>
      <run-list :jobs="jobs" :runs="runs" />
    </div>
  </div>
</template>
<script>
import { compactDateTime, statusClass } from "@/formatting.js";
import DimensionsSelector from "@/components/DimensionsSelector.vue";
import RunList from "@/components/RunList.vue";
import ParamsEditor from "@/components/ParamsEditor.vue";
export default {
  name: "view-job",
  components: {
    DimensionsSelector,
    RunList,
    ParamsEditor,
  },
  computed: {
    job_id() {
      return this.$store.state.current_job_id;
    },
    job() {
      return this.$store.state.current_job;
    },
    jobs() {
      return this.$store.state.jobs;
    },
    runs() {
      return this.$store.state.runs;
    },
  },
  mounted() {
    this.$store.dispatch("load_jobs");
    this.current_job();
  },
  watch: {
    $route: "current_job",
  },
  methods: {
    compactDateTime,
    statusClass,
    current_job() {
      if (!this.$route.params.job_id) {
        return;
      }
      this.$store.dispatch("load_job", this.$route.params.job_id);
      this.$store.dispatch("load_job_runs", {
        job_id: this.$route.params.job_id,
        newest: this.$route.query.newest
          ? new Date(this.$route.query.newest)
          : undefined,
      });
    },
    run_job_now() {
      this.$store.dispatch("run_job_now", this.$route.params.job_id);
    },
  },
};
</script>
<style scoped>
small {
  color: rgb(192, 192, 192);
}
</style>