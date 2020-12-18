<template>
  <div>
    <table class="table table-hover">
      <thead>
        <th scope="col" class="text-center">Status</th>
        <th scope="col">Name</th>
        <th scope="col">Dimensions</th>
        <th scope="col" />
      </thead>

      <tbody>
        <tr v-for="[id, job] in jobs" :key="id">
          <td class="status py-0 text-center align-middle">
            <i :class="statusClass(job.latest_run?.status)" />
          </td>
          <th scope="row">
            <router-link :to="`/job/${id}`">
              {{ job.name }}
            </router-link>
          </th>
          <td>
            <span
              class="dimensions"
              v-for="[dim, val] in Object.entries(job.dimensions || {})"
              :key="dim"
              >{{ dim }}={{ val }}&nbsp;</span
            >
          </td>
          <td class="text-right">
            <router-link :to="`/job/${id}/modify`">
              <i class="fas fa-edit text-primary" />
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { statusClass } from "@/formatting.js";
export default {
  name: "list-jobs",
  computed: {
    jobs() {
      return Object.entries(this.$store.state.jobs);
    },
  },
  mounted() {
    this.$store.dispatch("load_jobs", true);
  },
  methods: {
    statusClass,
  },
};
</script>

<style scoped>
.dimensions {
  color: lightgrey;
}
</style>
