<template>
  <table class="table table-sm table-responsive">
    <tbody>
      <tr v-for="[name, value] in Object.entries(selected)" :key="name">
        <td class="col-sm-3 align-middle">{{ name }}</td>
        <td class="col-sm px-3 align-middle">{{ value }}</td>
        <td class="col-sm-1">
          <button
            v-if="!readonly"
            type="button"
            name="delete-dimension"
            class="btn fas fa-trash-alt"
            @click="delete_dimension(name)"
          />
        </td>
      </tr>
      <tr v-if="readonly && Object.entries(selected).length == 0">
        <td class="text-muted" colspan="3">No dimensions selected</td>
      </tr>
      <tr v-if="!readonly">
        <td class="col-sm-3">
          <select name="new-name" class="custom-select" v-model="new_name">
            <option :value="null" hidden disabled>Select dimension</option>
            <option
              :value="id"
              v-for="id of Object.keys(available)"
              :key="id"
              :disabled="selected[id]"
            >
              {{ id }}
            </option>
          </select>
        </td>
        <td class="col-sm">
          <select name="new-value" class="custom-select" v-model="new_value">
            <option :value="null" hidden disabled>Select value</option>
            <option
              :value="value"
              v-for="value of Object.keys(available[new_name]?.values || {})"
              :key="value"
            >
              {{ value }}
            </option>
          </select>
        </td>
        <td class="col-sm-1">
          <button
            type="button"
            name="add-dimension"
            class="btn btn-secondary fas fa-plus-square btn-lg"
            @click="add_dimension()"
          />
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: "dimensions-selector",
  props: ["available", "selected", "readonly"],
  data() {
    return {
      new_name: null,
      new_value: null,
    };
  },
  methods: {
    add_dimension() {
      if (this.new_name !== null && this.new_value !== null) {
        this.$emit("add-dimension", this.new_name, this.new_value);
        this.new_name = null;
        this.new_value = null;
      }
    },
    delete_dimension(name) {
      if (this.new_name === null) {
        this.new_name = name;
        this.new_value = this.selected[name];
      }
      this.$emit("delete-dimension", name);
    },
  },
};
</script>