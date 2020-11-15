<template>
  <run-list :jobs="jobs" :runs="runs" />
</template>

<script>
import RunList from "@/components/RunList.vue";
export default {
  name: "list-runs",
  components: {
    RunList,
  },
  computed: {
    jobs() {
      return this.$store.state.jobs;
    },
    runs() {
      return this.$store.state.runs;
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
    load_runs_page() {
      if (this.$route.query.newest) {
        this.$store.dispatch("load_runs", new Date(this.$route.query.newest));
      } else {
        this.$store.dispatch("load_runs");
      }
    },
  },
};
</script>
