<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="`toast-${toast.type}`"
          @click="remove(toast.id)"
        >
          <span class="toast-icon">{{ icons[toast.type] }}</span>
          <span class="toast-message">{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

const { toasts, remove } = useToast()

const icons = {
  success: '✅',
  error:   '❌',
  info:    'ℹ️',
  warning: '⚠️'
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column-reverse;
  gap: 10px;
  max-width: 380px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  box-shadow: 0 8px 32px rgba(18, 78, 115, 0.18);
  cursor: pointer;
  pointer-events: all;
  backdrop-filter: blur(8px);
  border: 1px solid transparent;
}

.toast-success {
  background: #f0fdf4;
  color: #166534;
  border-color: #bbf7d0;
}

.toast-error {
  background: #fef2f2;
  color: #991b1b;
  border-color: #fecaca;
}

.toast-info {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  border-color: var(--color-primary);
}

.toast-warning {
  background: #fffbeb;
  color: #92400e;
  border-color: #fde68a;
}

.toast-icon {
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

.toast-message {
  flex: 1;
}

/* Transitions */
.toast-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}
</style>
