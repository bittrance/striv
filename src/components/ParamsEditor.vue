<template>
  <table class="table table-sm table-responsive">
    <tbody>
      <tr v-for="[name, value] in Object.entries(params)" :key="name">
        <template v-if="value.type == 'secret'">
          <td class="col-sm-3 align-middle">{{ name }}</td>
          <td class="col-sm-3">secret</td>
          <td class="col-sm px-3 align-middle text-secondary">
            &lt;redacted&gt;
          </td>
        </template>
        <template v-else>
          <td class="col-sm-3 align-middle">{{ name }}</td>
          <td class="col-sm-3">text</td>
          <td class="col-sm px-3 align-middle">{{ value }}</td>
        </template>
        <td class="col-sm-1">
          <button
            v-if="!readonly"
            type="button"
            name="delete-param"
            class="btn fas fa-trash-alt"
            @click="delete_param(name, value['type'] || 'text')"
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
        <td class="col-sm-3">
          <select name="param-type" class="custom-select" v-model="type">
            <option
              v-for="type in types"
              :key="type"
              :disabled="type == 'secret' && !public_key"
              :id="'param-type-' + type"
            >
              {{ type }}
            </option>
          </select>
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
import { encrypt_value } from "@/cryptutil";
export default {
  name: "params-editor",
  props: ["params", "readonly", "public_key"],
  data() {
    return {
      name: null,
      type: "text",
      value: null,
    };
  },
  computed: {
    types() {
      return ["text", "secret"];
    },
  },
  methods: {
    async add_param() {
      if (this.name !== null) {
        let value;
        if (this.type == "secret") {
          value = {
            type: "secret",
            encrypted: await encrypt_value(this.public_key, this.value),
          };
        } else {
          value = this.value;
        }
        this.$emit("add-param", this.name, value);
        this.name = null;
        this.type = "text";
        this.value = null;
      }
    },
    delete_param(name, type) {
      if (this.name === null && type != "secret") {
        this.name = name;
        this.type = "text";
        this.value = this.params[name];
      }
      this.$emit("delete-param", name);
    },
  },
};
</script>
