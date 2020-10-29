<template>
  <form @submit="create_job" class="py-3 px-3">
    <ValidationErrors v-if="error" v-bind:error="error" />
    <div class="form-group">
      <input
        id="name"
        type="text"
        placeholder="Job name"
        class="form-control"
        v-model="name"
      />
    </div>
    <div class="form-group">
      <select id="execution" class="custom-select" required v-model="execution">
        <option :value="null" hidden disabled>Select exection</option>
        <option :value="id" v-for="[id, execution] in executions" :key="id">
          {{ execution.name }}
        </option>
      </select>
    </div>
    <h2>Job-specific parameters</h2>
    <ParamsEditor
      v-bind:params="params"
      @add-param="add_param"
      @delete-param="delete_param"
    />
    <input type="submit" class="btn btn-primary" value="Create" />
    <router-link to="/jobs/preview" class="btn btn-secondary mx-3">
      Preview</router-link
    >
  </form>
</template>

<script>
import { useToast } from "vue-toastification";
import ParamsEditor from "./ParamsEditor.vue";
import ValidationErrors from "./ValidationErrors.vue";
export default {
  name: "modify-job",
  components: {
    ParamsEditor,
    ValidationErrors,
  },
  computed: {
    dimensions() {
      return Object.entries(this.$store.state.dimensions);
    },
    executions() {
      return Object.entries(this.$store.state.executions);
    },
    job() {
      return {
        name: this.name,
        execution: this.execution,
        params: this.params,
      };
    },
  },
  data() {
    return Object.assign(
      {
        name: null,
        execution: null,
        params: {},
        error: null,
      },
      this.$store.state.current_job
    );
  },
  watch: {
    job: {
      deep: true,
      handler: function (job) {
        this.$store.dispatch("current_job", JSON.parse(JSON.stringify(job)));
      },
    },
  },
  setup() {
    return { toast: useToast() };
  },
  methods: {
    add_param(name, value) {
      this.params[name] = value;
    },
    async create_job(event) {
      event.preventDefault();
      await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-type": "application/json" },
        body: JSON.stringify(this.job),
      })
        .then(async (response) => {
          const result = await response.json();
          if (response.ok) {
            this.toast.success(`New job created: ${result.id}`, {
              timeout: 3000,
            });
            this.$router.push({ path: "/" });
          } else {
            console.log(result);
            this.error = result;
          }
        })
        .catch((err) => {
          this.toast.error(`Oops! ${err.message}`);
        });
    },
    delete_param(name) {
      delete this.params[name];
    },
  },
  mounted() {
    this.$store.dispatch("load_state");
  },
};
</script>