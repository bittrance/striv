<template>
  <form class="job" @submit="create_job">
    <h1>Create a new job</h1>
    <p v-if="error">
      Validation errors:
      <ul> 
        <li v-for="[field, message] in Object.entries(error)" :key="field">
          <span>{{ field }}</span>
          <span>{{ message[0] }}</span>
        </li>
      </ul>
    </p>
    <p>
      <label for="name">Name</label>
      <input id="name" type="text" v-model="name" />
    </p>
    <p>
      <label for="execution">Execution</label>
      <select id="execution" v-model="execution">
        <option :value="id" v-for="[id, execution] in executions" :key="id">
          {{ execution.name }}
        </option>
      </select>
    </p>
    <input type="submit" value="Create" />
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