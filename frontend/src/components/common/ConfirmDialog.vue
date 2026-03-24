<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="confirm-overlay" @click.self="cancel">
        <div class="confirm-dialog">
          <div class="confirm-icon">{{ icon }}</div>
          <h3 class="confirm-title">{{ title }}</h3>
          <p class="confirm-message">{{ message }}</p>
          <div class="confirm-actions">
            <button class="btn btn-secondary" @click="cancel">{{ cancelText }}</button>
            <button class="btn" :class="confirmClass" @click="confirm">{{ confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const visible = ref(false)
const title = ref('')
const message = ref('')
const icon = ref('🗑️')
const confirmText = ref('Удалить')
const cancelText = ref('Отмена')
const confirmClass = ref('btn-danger')

let resolvePromise = null

function open(options = {}) {
  title.value = options.title || 'Подтверждение'
  message.value = options.message || 'Вы уверены?'
  icon.value = options.icon || '⚠️'
  confirmText.value = options.confirmText || 'Подтвердить'
  cancelText.value = options.cancelText || 'Отмена'
  confirmClass.value = options.danger ? 'btn-danger' : 'btn-primary'
  visible.value = true
  return new Promise(res => { resolvePromise = res })
}

function confirm() {
  visible.value = false
  resolvePromise?.(true)
}

function cancel() {
  visible.value = false
  resolvePromise?.(false)
}

defineExpose({ open })
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
}

.confirm-dialog {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: var(--spacing);
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 0 24px 60px rgba(18, 78, 115, 0.2);
  border: 1px solid var(--color-border);
}

.confirm-icon {
  font-size: 40px;
  margin-bottom: var(--spacing-xs);
}

.confirm-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-xxs);
}

.confirm-message {
  color: var(--color-text-light);
  font-size: 15px;
  margin-bottom: var(--spacing);
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: var(--spacing-xs);
  justify-content: center;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
  transform: translateY(-2px);
}

/* Transitions */
.modal-enter-active, .modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .confirm-dialog { transform: scale(0.9); }
.modal-leave-to .confirm-dialog { transform: scale(0.9); }
</style>
