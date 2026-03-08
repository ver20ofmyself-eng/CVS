<template>
  <div class="register-view">
    <div class="container">
      <div class="auth-wrapper">
        <RegisterForm />
      </div>
    </div>
  </div>
</template>

<script setup>
import RegisterForm from '@/components/auth/RegisterForm.vue'
</script>

<style scoped>
.register-view {
  min-height: calc(100vh - 140px);
  display: flex;
  align-items: center;
  padding: var(--spacing) 0;
}

.auth-wrapper {
  width: 100%;
  animation: slideUp 0.5s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
