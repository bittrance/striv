<template>
  <div>
    <div class="row px-3 py-3">
      <div class="col-sm">
        <small>Job name</small>
        <div>{{ job.name }}</div>
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
      this.$store.dispatch("load_job", this.$route.params.job_id);
      this.$store.dispatch("load_job_runs", {
        job_id: this.$route.params.job_id,
        newest: this.$route.query.newest
          ? new Date(this.$route.query.newest)
          : undefined,
      });
    },
  },
};
</script>
<style scoped>
small {
  color: rgb(192, 192, 192);
}
</style>