<template>
  <div>
    <div class="text-center">
      <router-link class="btn text-primary" :to="this.$route.path">
        <i class="fas fa-angle-double-left fa-2x" />
      </router-link>
      {{ compactDateTime(this.newest) || "Now" }} &mdash;
      {{ compactDateTime(this.oldest) }}
      <router-link
        class="btn text-primary"
        :to="`${this.$route.path}?newest=${this.oldest?.toISOString()}`"
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
        <tr v-for="[id, run] in sorted_runs" :key="id">
          <td class="status py-0 text-center align-middle">
            <i :class="statusClass(run.status)" />
          </td>
          <th class="text-nowrap" scope="row">
            <router-link :to="`/run/${id}`">
              {{ jobs[run.job_id]?.name }}
            </router-link>
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
  name: "run-list",
  props: ["jobs", "runs"],
  computed: {
    newest() {
      return this.sorted_runs.length > 0
        ? this.sorted_runs[0][1].created_at
        : undefined;
    },
    oldest() {
      return this.sorted_runs.length > 0
        ? this.sorted_runs[this.sorted_runs.length - 1][1].created_at
        : undefined;
    },
    sorted_runs() {
      return Object.entries(this.runs).sort((l, r) =>
        l[1].created_at > r[1].created_at ? -1 : 1
      );
    },
  },
  methods: {
    compactDateTime,
    statusClass,
  },
};
</script>
<style scoped>
.status {
  font-size: 1.5rem;
  width: 3rem;
}
</style>