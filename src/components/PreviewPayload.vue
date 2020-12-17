<template>
  <div class="mx-3">
    <ValidationErrors v-if="is_error" v-bind:error="evaluation" />
    <h2>Effective parameters</h2>
    <params-editor :params="evaluation.params || {}" :readonly="true" />
    <h2>Evaluated template</h2>
    <blockquote v-if="!is_error" style="white-space: pre">
      {{ evaluation.payload }}
    </blockquote>
    <div v-else class="text-muted">Errors prevent evaluation</div>
    <a @click="$router.back()" class="btn btn-secondary d-lg-none">Back</a>
  </div>
</template>
<script>
import ParamsEditor from "@/components/ParamsEditor.vue";
import ValidationErrors from "./ValidationErrors.vue";

export default {
  name: "preview-payload",
  components: {
    ParamsEditor,
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
    this.current_job();
  },
  watch: {
    "$store.state.current_job": "current_job",
  },
  methods: {
    current_job() {
      this.$store.dispatch("current_job", this.$store.state.current_job);
    },
  },
};
</script>