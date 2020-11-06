<template>
  <div class="px-3 py-3">
    <table class="table table-hover">
      <thead>
        <th scope="col">Name</th>
        <th scope="col">Dimensions</th>
        <th scope="col" />
      </thead>

      <tbody>
        <tr v-for="[id, job] in jobs" :key="id">
          <th scope="row">
            {{ job.name }}
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
            <router-link v-bind:to="'/job/' + id"
              ><i class="fas fa-edit text-secondary"></i
            ></router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: "list-jobs",
  computed: {
    jobs() {
      return Object.entries(this.$store.state.jobs);
    },
  },
  mounted() {
    this.$store.dispatch("load_jobs");
  },
};
</script>

<style scoped>
.dimensions {
  color: lightgrey;
}
</style>
