<template>
  <div id="neo-app">
    <router-view />
  </div>
</template>

<script setup>
// Root shell – routing handles all layout decisions
</script>

<style>
#neo-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
