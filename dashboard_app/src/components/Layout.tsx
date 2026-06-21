import { useCallback } from "react"
import Sidebar from "./Sidebar"
import Header from "./Header"
import ToastContainer from "./Toast"
import { useAppDispatch, useAppState } from "../context/AppContext"
import { useWebSocket } from "../hooks/useWebSocket"
import { ToastContext, useToastState } from "../hooks/useToast"
import { useHashLocation } from "../hooks/useHashLocation"
import DashboardPage from "../pages/DashboardPage"
import CamerasPage from "../pages/CamerasPage"
import EventsPage from "../pages/EventsPage"
import ReportsPage from "../pages/ReportsPage"
import SettingsPage from "../pages/SettingsPage"
import type { AlertMessage } from "../types"

export default function Layout() {
  const dispatch = useAppDispatch()
  const { connected } = useAppState()
  const toastState = useToastState()
  const [location] = useHashLocation()

  const handleAlert = useCallback((alert: AlertMessage) => {
    dispatch({
      type: 'ADD_EVENT',
      event: {
        timestamp: alert.timestamp,
        camera_id: alert.camera_id,
        event_type: alert.event_type,
        confidence: alert.confidence,
        details: { snapshot_b64: alert.snapshot_b64 ?? null },
      },
    })
    const labels: Record<string, string> = { fall: '낙상', elopement: '이탈', loitering: '배회', stranger: '미등록 외부인' }
    toastState.toast(
      `${labels[alert.event_type] ?? alert.event_type} 감지`,
      { message: `${alert.camera_id} · 신뢰도 ${(alert.confidence * 100).toFixed(0)}%`, type: 'alert' }
    )
  }, [dispatch, toastState])

  const handleConnectionChange = useCallback((c: boolean) => {
    dispatch({ type: 'SET_CONNECTED', connected: c })
  }, [dispatch])

  useWebSocket(handleAlert, handleConnectionChange)

  const Page = location.startsWith('/cameras')  ? CamerasPage
             : location.startsWith('/events')   ? EventsPage
             : location.startsWith('/reports')  ? ReportsPage
             : location.startsWith('/settings') ? SettingsPage
             : DashboardPage

  return (
    <ToastContext.Provider value={toastState}>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar connected={connected} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
          <Header connected={connected} />
          <main style={{ flex: 1, overflow: 'auto' }}>
            <Page />
          </main>
        </div>
      </div>
      <ToastContainer toasts={toastState.toasts} onDismiss={toastState.dismiss} />
    </ToastContext.Provider>
  )
}
