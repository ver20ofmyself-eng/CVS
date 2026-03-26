<template>
  <div class="vacancy-edit-view">
    <div class="container">
      <!-- Хлебные крошки -->
      <div class="breadcrumbs">
        <router-link to="/vacancies" class="breadcrumb-link">
          ← К списку вакансий
        </router-link>
      </div>

      <!-- Заголовок -->
      <h1 class="page-title">
        {{ isEditing ? 'Редактирование вакансии' : 'Создание новой вакансии' }}
      </h1>

      <!-- Форма -->
      <VacancyForm :vacancy-id="vacancyId" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import VacancyForm from '@/components/vacancies/VacancyForm.vue'

const route = useRoute()
const vacancyId = computed(() => route.params.id ? parseInt(route.params.id) : null)
const isEditing = computed(() => !!vacancyId.value)
</script>

<style scoped>
.vacancy-edit-view {
  padding: var(--spacing) 0;
  min-height: calc(100vh - 140px);
}

.breadcrumbs {
  margin-bottom: var(--spacing);
}

.breadcrumb-link {
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 14px;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
}

.breadcrumb-link:hover {
  color: var(--color-primary);
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing);
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }
}
</style>
