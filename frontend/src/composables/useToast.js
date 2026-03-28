/**
 * Глобальный сервис уведомлений (Toast)
 * Использование: import { useToast } from '@/composables/useToast'
 */
import { reactive } from 'vue'

const state = reactive({
  toasts: []
})

let nextId = 1

function add(message, type = 'info', duration = 4000) {
  const id = nextId++
  state.toasts.push({ id, message, type })
  if (duration > 0) setTimeout(() => remove(id), duration)
  return id
}

function remove(id) {
  const idx = state.toasts.findIndex(t => t.id === id)
  if (idx !== -1) state.toasts.splice(idx, 1)
}

export function useToast() {
  return {
    toasts: state.toasts,
    success: (msg, d) => add(msg, 'success', d),
    error:   (msg, d) => add(msg, 'error', d),
    info:    (msg, d) => add(msg, 'info', d),
    warning: (msg, d) => add(msg, 'warning', d),
    remove
  }
}
