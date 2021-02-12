<template>
  <div class="px-3 py-3">
    <div class="mb-4 media">
      <i
        class="ml-2 mr-4 align-self-center"
        :class="statusClass(run.status)"
        style="font-size: 2.5rem"
      />
      <div class="row media-body">
        <div class="col">
          <small>Job</small>
          <div>
            {{ job.name }}
            <router-link
              :to="`/job/${run.job_id}/modify`"
              class="btn text-primary mb-1"
              ><i class="fas fa-edit"></i
            ></router-link>
          </div>
        </div>
        <div class="w-100 mb-2" />
        <div class="col">
          <small class="d-inline-block">Status</small>
          <div>{{ run.status?.replace(/^\w/, (c) => c.toUpperCase()) }}</div>
        </div>
        <div class="col">
          <small>Created at</small>
          <div>{{ compactDateTime(run.created_at) }}</div>
        </div>
        <div class="col">
          <small>Started at</small>
          <div>{{ compactDateTime(run.started_at) }}</div>
        </div>
        <div class="col">
          <small>Finished at</small>
          <div>{{ compactDateTime(run.finished_at) }}</div>
        </div>
        <div class="col">
          <small>Duration</small>
          <div>{{ run.duration }}</div>
        </div>
      </div>
    </div>
    <div>
      <div v-for="[name, payload] in logs" :key="name" class="mb-4">
        <h2>
          {{ name }}
          <router-link
            v-if="payload.trim().length"
            :to="is_compact(name) ? `?expand=${encodeURIComponent(name)}` : ''"
            class="btn text-primary"
          >
            <i class="fas fa-expand-alt" />
          </router-link>
          <span v-else>&mdash; empty</span>
        </h2>
        <div
          v-if="payload.trim().length"
          :class="{ 'log-container': is_compact(name) }"
          class="bg-light w-100"
        >
          <pre v-if="is_compact(name)">{{ payload.trim() }}</pre>
          <pre v-else>{{ full_log }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { compactDateTime, statusClass } from "@/formatting.js";
export default {
  name: "view-run",
  data() {
    return {
      full_log: null,
    };
  },
  computed: {
    job() {
      return this.$store.state.current_job;
    },
    run() {
      return this.$store.state.current_run;
    },
    logs() {
      return Object.entries(this.$store.state.current_run_logs);
    },
  },
  mounted() {
    this.current_run();
  },
  watch: {
    $route: "current_run",
  },
  methods: {
    compactDateTime,
    statusClass,
    async current_run() {
      if (!this.$route.params.run_id) {
        return;
      }
      this.$store.dispatch("load_run", this.$route.params.run_id);
      if (this.$route.query.expand) {
        this.full_log = await this.$store.dispatch("load_log", {
          run_id: this.$route.params.run_id,
          logname: this.$route.query.expand,
        });
      }
    },
    is_compact(logname) {
      return this.$route.query.expand != logname;
    },
  },
};
</script>
<style scoped>
small {
  color: rgb(192, 192, 192);
}
.log-container {
  overflow: hidden;
}
</style>