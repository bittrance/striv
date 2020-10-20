<template>
  <div>
    <h1>striv</h1>
    <ul class="nav nav-tabs">
      <li class="nav-item ml-3">
        <router-link to="/" class="nav-link" active-class="active"
          >Jobs</router-link
        >
      </li>
      <li class="nav-item">
        <router-link to="/jobs/new" class="nav-link" active-class="active"
          >New job</router-link
        >
      </li>
    </ul>
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",
};
</script>

