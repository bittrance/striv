<template>
  <Jobs />
</template>

<script>
import Jobs from "./components/Jobs.vue";

export default {
  name: "App",
  components: {
    Jobs,
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
