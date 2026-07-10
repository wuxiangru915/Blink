import { reactive } from 'vue'

export function useToast() {
  const toast = reactive({ show: false, message: '', type: 'success' })
  let toastTimer = null

  function showToast(message, type = 'success') {
    clearTimeout(toastTimer)
    toast.show = true
    toast.message = message
    toast.type = type
    toastTimer = setTimeout(() => { toast.show = false }, 2500)
  }

  return { toast, showToast }
}
