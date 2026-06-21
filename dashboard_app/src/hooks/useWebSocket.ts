import { useCallback, useEffect, useRef } from "react"
import type { AlertMessage } from "../types"
import { WS_BASE } from "../lib/utils"

export function useWebSocket(
  onAlert: (alert: AlertMessage) => void,
  onConnectionChange?: (connected: boolean) => void,
) {
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 콜백을 ref로 유지 — 렌더마다 새 함수가 와도 WS를 재연결하지 않음
  const onAlertRef = useRef(onAlert)
  const onConnectionChangeRef = useRef(onConnectionChange)
  useEffect(() => {
    onAlertRef.current = onAlert
    onConnectionChangeRef.current = onConnectionChange
  })

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) return

    const ws = new WebSocket(`${WS_BASE}/ws/alerts`)

    ws.onopen = () => {
      onConnectionChangeRef.current?.(true)
    }
    ws.onclose = () => {
      onConnectionChangeRef.current?.(false)
      retryRef.current = setTimeout(connect, 3000)
    }
    ws.onerror = () => {
      onConnectionChangeRef.current?.(false)
    }
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === "alert") onAlertRef.current(data)
      } catch { /* ignore */ }
    }
    wsRef.current = ws
  }, []) // 의존성 없음 — ref로 최신 콜백 참조

  useEffect(() => {
    connect()
    return () => {
      if (retryRef.current) clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [connect])
}
