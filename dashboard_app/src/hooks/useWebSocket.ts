import { useCallback, useEffect, useRef, useState } from "react"
import type { AlertMessage } from "../types"
import { WS_BASE } from "../lib/utils"

export function useWebSocket(onAlert: (alert: AlertMessage) => void) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/alerts`)
    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, 2000)
    }
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === "alert") onAlert(data)
      } catch { /* ignore */ }
    }
    wsRef.current = ws
  }, [onAlert])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])

  return { connected }
}
