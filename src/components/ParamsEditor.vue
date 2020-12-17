<template>
  <div class="container-fluid form-group">
    <template v-for="[name, value] in Object.entries(params)" :key="name">
      <div class="row mb-1">
        <div class="col-sm-6 px-0 align-middle">
          <strong>{{ name }}</strong>
        </div>
        <div
          v-if="value._striv_type == 'secret'"
          class="col-sm px-0 text-secondary"
        >
          <span v-if="!readonly" class="text-muted">secret: </span>
          &lt;redacted&gt;
        </div>
        <blockquote v-else class="col-sm px-0" style="white-space: pre">
          <span v-if="!readonly" class="text-muted">text: </span>{{ value }}
        </blockquote>
        <div class="col-sm-1 px-0 text-sm-right">
          <button
            v-if="!readonly"
            type="button"
            name="delete-param"
            class="btn btn-lg border fas fa-trash-alt"
            @click="delete_param(name, value['_striv_type'] || 'text')"
          />
        </div>
      </div>
    </template>
    <div v-if="readonly && Object.entries(params).length == 0" class="row">
      <div class="col text-muted px-0">No parameters provided</div>
    </div>
    <template v-if="!readonly">
      <h3 class="row">New parameter</h3>
      <div class="row">
        <div class="col-sm px-0">
          <div class="container-fluid">
            <div class="row">
              <div class="col-sm px-0 mr-sm-3">
                <input
                  type="text"
                  name="param-name"
                  class="form-control"
                  placeholder="Parameter"
                  v-model="name"
                />
              </div>
              <div class="col-sm-3 px-0">
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
              </div>
            </div>
            <div class="row">
              <div class="col-sm px-0 pt-sm-2">
                <textarea
                  name="param-value"
                  class="form-control"
                  placeholder="Value"
                  v-model="value"
                />
              </div>
            </div>
          </div>
        </div>
        <div class="col-sm-1 px-0 text-sm-right">
          <button
            type="button"
            name="add-param"
            class="btn btn-secondary fas fa-plus btn-lg"
            @click="add_param()"
          />
        </div>
      </div>
    </template>
  </div>
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
            _striv_type: "secret",
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
