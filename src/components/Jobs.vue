<template>
  <table class="jobs">
    <tbody>
      <tr v-for="[id, job] in jobs" :key="id">
        <td>{{ job.name }}</td>
        <td>
          <span
            class="dimensions"
            v-for="[dim, val] in Object.entries(job.dimensions)"
            :key="dim"
            >{{ dim }}={{ val }}</span
          >
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: "Jobs",
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
