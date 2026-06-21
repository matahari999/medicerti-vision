import { createContext, useCallback, useContext, useRef, useState } from "react"
import type { Toast } from "../types"

interface ToastCtxType {
  toasts: Toast[]
  toast: (title: string, opts?: { message?: string; type?: Toast['type']; duration?: number }) => void
  dismiss: (id: number) => void
}

export const ToastContext = createContext<ToastCtxType>({
  toasts: [],
  toast: () => {},
  dismiss: () => {},
})

export function useToastState(): ToastCtxType {
  const [toasts, setToasts] = useState<Toast[]>([])
  const idRef = useRef(0)

  const toast = useCallback((title: string, opts: { message?: string; type?: Toast['type']; duration?: number } = {}) => {
    const id = ++idRef.current
    const duration = opts.duration ?? 4000
    setToasts(prev => [...prev.slice(-4), { id, title, message: opts.message, type: opts.type ?? 'info', duration }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration)
  }, [])

  const dismiss = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toasts, toast, dismiss }
}

export const useToast = () => useContext(ToastContext)
