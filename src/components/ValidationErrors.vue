<template>
  <div style="color: red">
    <p v-if="error['invalid-fields']">
      {{ error.title }}
      <ul>
        <li v-for="[field, message] in Object.entries(error['invalid-fields'])" :key="field">
          <span>{{ field }}: {{ message[0] }}</span>
        </li>
      </ul>
    </p>
    <p v-if="error.source">
      {{ error.title }}
      <span>{{ error.detail }}</span>
    </p>
  </div>
</template>

<script>
export default {
  name: "ValidationErrors",
  props: ["error"],
};
</script>