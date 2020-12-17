<template>
  <form @submit="create_job" class="py-3 px-3">
    <div class="container-fluid">
      <div class="row">
        <div class="col">
          <ValidationErrors v-if="error" v-bind:error="error" />
          <h2>Job data</h2>
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
            <select
              id="execution"
              class="custom-select"
              required
              v-model="execution"
            >
              <option :value="null" hidden disabled>Select execution</option>
              <option
                :value="id"
                v-for="[id, execution] in executions"
                :key="id"
              >
                {{ execution.name }}
              </option>
            </select>
          </div>
          <h2>Dimensions</h2>
          <dimensions-selector
            v-bind:available="available_dimensions"
            v-bind:selected="dimensions"
            @add-dimension="add_dimension"
            @delete-dimension="delete_dimension"
          />
          <h2>Job-specific parameters</h2>
          <params-editor
            v-bind:params="params"
            v-bind:public_key="public_key"
            @add-param="add_param"
            @delete-param="delete_param"
          />
          <div class="row px-3 mt-3">
            <input
              type="submit"
              class="btn btn-primary"
              value="Create"
              v-if="is_create"
            />
            <input
              type="submit"
              class="btn btn-primary"
              value="Modify"
              v-if="!is_create"
            />
            <router-link
              to="/jobs/preview"
              class="btn btn-secondary d-lg-none mx-3"
            >
              Preview</router-link
            >
          </div>
        </div>
        <div class="col-4 pl-0 d-none d-lg-block bg-light text-muted">
          <preview-payload />
        </div>
      </div>
    </div>
  </form>
</template>

<script>
import { useToast } from "vue-toastification";
import DimensionsSelector from "@/components/DimensionsSelector.vue";
import ParamsEditor from "./ParamsEditor.vue";
import PreviewPayload from "@/components/PreviewPayload.vue";
import ValidationErrors from "./ValidationErrors.vue";
function store_param(param, defaultValue) {
  return {
    get() {
      return this.$store.state.current_job[param] || defaultValue;
    },
    set(value) {
      let job = JSON.parse(JSON.stringify(this.$store.state.current_job));
      job[param] = value;
      this.$store.dispatch("current_job", job);
    },
  };
}
export default {
  name: "modify-job",
  components: {
    DimensionsSelector,
    ParamsEditor,
    PreviewPayload,
    ValidationErrors,
  },
  computed: {
    is_create() {
      return this.$store.state.current_job_id == undefined;
    },
    available_dimensions() {
      return this.$store.state.dimensions;
    },
    executions() {
      return Object.entries(this.$store.state.executions);
    },
    public_key() {
      return this.$store.state.public_key;
    },
    name: store_param("name"),
    execution: store_param("execution"),
    dimensions: store_param("dimensions", {}),
    params: store_param("params", {}),
  },
  data() {
    return {
      error: null,
    };
  },
  setup() {
    return { toast: useToast() };
  },
  mounted() {
    this.$store.dispatch("load_state");
    this.$store.dispatch("load_public_key");
    this.current_job();
  },
  watch: {
    $route: "current_job",
  },
  methods: {
    add_dimension(name, value) {
      let new_selection = Object.assign({}, this.dimensions);
      new_selection[name] = value;
      this.dimensions = new_selection;
    },
    add_param(name, value) {
      let new_params = Object.assign({}, this.params);
      new_params[name] = value;
      this.params = new_params;
    },
    current_job() {
      if (this.$route.params.job_id) {
        this.$store.dispatch("load_job", this.$route.params.job_id);
      } else {
        this.$store.commit("current_job_id", undefined);
      }
    },
    async create_job(event) {
      event.preventDefault();
      this.$store
        .dispatch("store_current_job")
        .then(async (response) => {
          const result = await response.json();
          if (response.ok) {
            if (this.is_create) {
              this.toast.success(`New job created: ${result.id}`, {
                timeout: 3000,
              });
            } else {
              this.toast.success(`Job updated: ${result.id}`, {
                timeout: 3000,
              });
            }
            this.$router.push({ path: "/" });
          } else {
            this.error = result;
          }
        })
        .catch((err) => {
          this.toast.error(`Oops! ${err.message}`);
        });
    },
    delete_dimension(name) {
      let new_selection = Object.assign({}, this.dimensions);
      delete new_selection[name];
      this.dimensions = new_selection;
    },
    delete_param(name) {
      let new_params = Object.assign({}, this.params);
      delete new_params[name];
      this.params = new_params;
    },
  },
};
</script>
