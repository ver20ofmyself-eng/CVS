<template>
  <div class="vacancies-view">
    <div class="container">
      <VacancyList />
    </div>
  </div>
</template>

<script setup>
import VacancyList from '@/components/vacancies/VacancyList.vue'
</script>

<style scoped>
.vacancies-view {
  padding: var(--spacing) 0;
  min-height: calc(100vh - 140px);
}
</style>
