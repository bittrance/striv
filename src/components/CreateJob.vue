<template>
  <form @submit="create_job" class="py-3 px-3">
    <p v-if="error" style="color: red">
      Validation errors:
      <ul>
        <li v-for="[field, message] in Object.entries(error)" :key="field">
          <span>{{ field }}: {{ message[0] }}</span>
        </li>
      </ul>
    </p>
    <div class="form-group">
      <input id="name" type="text" placeholder="Job name" class="form-control" v-model="name" />
    </div>
    <div class="form-group">
      <select id="execution" class="custom-select" required v-model="execution">
        <option :value="null" hidden disabled>Select exection</option>
        <option :value="id" v-for="[id, execution] in executions" :key="id">
          {{ execution.name }}
        </option>
      </select>
    </div>
    <input type="submit" class="btn btn-primary" value="Create" />
  </form>
</template>

<script>
import { useToast } from "vue-toastification";
export default {
  name: "CreateJob",
  computed: {
    executions() {
      return Object.entries(this.$store.state.executions);
    },
  },
  data() {
    return {
      name: null,
      execution: null,
      error: null,
    };
  },
  setup() {
    return { toast: useToast() };
  },
  methods: {
    async create_job(event) {
      event.preventDefault();
      await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-type": "application/json" },
        body: JSON.stringify({
          name: this.name,
          execution: this.execution,
        }),
      })
        .then(async (response) => {
          const result = await response.json();
          if (response.ok) {
            this.toast.success(`New job created: ${result.id}`, {
              timeout: 3000,
            });
            this.$router.push({ path: "/" });
          } else {
            this.error = result;
          }
        })
        .catch((err) => {
          this.toast.error(`Oops! ${err.message}`);
        });
    },
  },
  mounted() {
    this.$store.dispatch("load_state");
  },
};
</script>