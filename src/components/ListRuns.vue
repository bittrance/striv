<template>
  <div class="px-3 py-3">
    <div class="text-center">
      <router-link class="btn text-primary" to="/runs">
        <i class="fas fa-angle-double-left fa-2x" />
      </router-link>
      {{ compactDateTime(this.newest) || "Now" }} &mdash;
      {{ compactDateTime(this.oldest) }}
      <router-link
        class="btn text-primary"
        :to="`/runs?newest=${this.oldest?.toISOString()}`"
      >
        <i class="fas fa-angle-right fa-2x" />
      </router-link>
    </div>
    <table class="table table-hover">
      <thead>
        <th scope="col" class="text-center">Job</th>
        <th scope="col">Status</th>
        <th scope="col" class="text-right">Started at</th>
        <th scope="col" class="text-right">Duration</th>
      </thead>
      <tbody>
        <tr v-for="[id, run] in runs" :key="id">
          <td class="status py-0 text-center align-middle">
            <i :class="statusClass(run.status)" />
          </td>
          <th class="text-nowrap" scope="row">
            <router-link :to="`/run/${id}`">{{
              this.$store.state?.jobs[run.job_id]?.name
            }}</router-link>
          </th>
          <td class="text-right">
            {{ run.started_at ? compactDateTime(run.started_at) : "&mdash;" }}
          </td>
          <td class="text-right">{{ run.duration }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { compactDateTime, statusClass } from "@/formatting.js";
export default {
  name: "list-runs",
  computed: {
    newest() {
      return this.$route.query.newest
        ? new Date(this.$route.query.newest)
        : undefined;
    },
    oldest() {
      return this.runs.length > 0
        ? this.runs[this.runs.length - 1][1].created_at
        : undefined;
    },
    runs() {
      return Object.entries(this.$store.state.runs).sort((l, r) =>
        l[1].created_at > r[1].created_at ? -1 : 1
      );
    },
  },
  mounted() {
    this.$store.dispatch("load_jobs");
    this.load_runs_page();
  },
  watch: {
    $route: "load_runs_page",
  },
  methods: {
    compactDateTime,
    statusClass,
    load_runs_page() {
      if (this.newest) {
        this.$store.dispatch("load_runs", this.newest);
      } else {
        this.$store.dispatch("load_runs");
      }
    },
  },
};
</script>
<style scoped>
.status {
  font-size: 1.5rem;
  width: 3rem;
}
</style>