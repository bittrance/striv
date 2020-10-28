<template>
  <div class="mx-3">
    <ValidationErrors v-if="is_error" v-bind:error="evaluation" />
    <blockquote v-if="!is_error">{{ evaluation.payload }}</blockquote>
    <router-link to="/jobs/new" class="btn btn-secondary">Back</router-link>
  </div>
</template>
<script>
import ValidationErrors from "./ValidationErrors.vue";

export default {
  name: "PreviewPayload",
  components: {
    ValidationErrors,
  },
  computed: {
    is_error() {
      return (
        this.$store.state.current_job_evaluation &&
        !this.$store.state.current_job_evaluation.payload
      );
    },
    evaluation() {
      return this.$store.state.current_job_evaluation || {};
    },
  },
  mounted() {
    // Trigger evaluation
    this.$store.dispatch("current_job", this.$store.state.current_job);
  },
};
</script>