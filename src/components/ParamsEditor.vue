<template>
  <table class="table table-sm table-responsive">
    <tbody>
      <tr v-for="[name, value] in Object.entries(params)" :key="name">
        <td class="col-sm-3 align-middle">{{ name }}</td>
        <td class="col-sm px-3 align-middle">{{ value }}</td>
        <td class="col-sm-1">
          <button
            v-if="!readonly"
            type="button"
            name="delete-param"
            class="btn fas fa-trash-alt"
            @click="delete_param(name)"
          />
        </td>
      </tr>
      <tr v-if="readonly && Object.entries(params).length == 0">
        <td colspan="3">No parameters provided</td>
      </tr>
      <tr v-if="!readonly">
        <td class="col-sm-3">
          <input
            type="text"
            name="param-name"
            class="form-control"
            placeholder="Parameter"
            v-model="name"
          />
        </td>
        <td class="col-sm">
          <input
            type="text"
            name="param-value"
            class="form-control"
            placeholder="Value"
            v-model="value"
          />
        </td>
        <td class="col-sm-1">
          <button
            type="button"
            name="add-param"
            class="btn btn-secondary fas fa-plus-square btn-lg"
            @click="add_param()"
          />
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: "params-editor",
  props: ["params", "readonly"],
  data() {
    return {
      name: null,
      value: null,
    };
  },
  methods: {
    add_param() {
      if (this.name !== null) {
        this.$emit("add-param", this.name, this.value);
        this.name = null;
        this.value = null;
      }
    },
    delete_param(name) {
      if (this.name === null) {
        this.name = name;
        this.value = this.params[name];
      }
      this.$emit("delete-param", name);
    },
  },
};
</script>