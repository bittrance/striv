<template>
  <div class="container-fluid form-group">
    <div
      v-for="[name, value] in Object.entries(selected)"
      :key="name"
      class="row mb-3"
    >
      <div class="col-sm-3 px-0 mr-sm-3">
        <strong>{{ name }}</strong>
      </div>
      <div class="col-sm px-0 mr-sm-3">{{ value }}</div>
      <div class="col-sm-1 px-0 text-sm-right">
        <button
          v-if="!readonly"
          type="button"
          name="delete-dimension"
          class="btn btn-lg border fas fa-trash-alt"
          @click="delete_dimension(name)"
        />
      </div>
    </div>
    <div v-if="readonly && Object.entries(selected).length == 0" class="row">
      <div class="col text-muted px-0">No dimensions selected</div>
    </div>
    <template v-if="!readonly">
      <h3 class="row">Add dimension</h3>
      <div class="row">
        <div class="col-sm-3 px-0 mr-sm-3">
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
        </div>
        <div class="col-sm px-0">
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
        </div>
        <div class="col-sm-1 px-0 text-sm-right">
          <button
            type="button"
            name="add-dimension"
            class="btn btn-secondary fas fa-plus btn-lg"
            @click="add_dimension()"
          />
        </div>
      </div>
    </template>
  </div>
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