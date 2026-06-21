import { useCallback, useRef, useState } from "react"
import Header from "./components/Header"
import StatsCards from "./components/StatsCards"
import EventList from "./components/EventList"
import MainPanel from "./components/MainPanel"
import SettingsPanel from "./components/SettingsPanel"
import type { AlertMessage, EventStats, DetectionEvent, ZoomInfo } from "./types"
import { useWebSocket } from "./hooks/useWebSocket"

const typeLabels: Record<string, string> = {
  fall: "낙상", elopement: "이탈", loitering: "배회", stranger: "미등록 외부인",
}

export default function App() {
  const [events, setEvents] = useState<DetectionEvent[]>([])
  const [stats, setStats] = useState<EventStats>({ fall: 0, elopement: 0, loitering: 0, stranger: 0 })
  const [zoomInfo, setZoomInfo] = useState<ZoomInfo>({ active: false, zoom_factor: 2.0, center: null })
  const [showSettings, setShowSettings] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<DetectionEvent | null>(null)
  const eventIdRef = useRef(0)

  const handleAlert = useCallback((alert: AlertMessage) => {
    setStats((prev) => ({
      ...prev,
      [alert.event_type]: (prev[alert.event_type as keyof EventStats] || 0) + 1,
    }))
    const ev: DetectionEvent = {
      id: ++eventIdRef.current,
      timestamp: alert.timestamp,
      camera_id: alert.camera_id,
      event_type: alert.event_type,
      confidence: alert.confidence,
      details: { snapshot_b64: alert.snapshot_b64 },
    }
    setEvents((prev) => [ev, ...prev].slice(0, 200))
  }, [])

  const { connected } = useWebSocket(handleAlert)

  return (
    <div className="h-screen flex flex-col">
      <Header
        connected={connected}
        onToggleSettings={() => setShowSettings(!showSettings)}
        showSettings={showSettings}
      />
      <div className="flex flex-1 overflow-hidden">
        {showSettings ? (
          <SettingsPanel onClose={() => setShowSettings(false)} zoomInfo={zoomInfo} onZoomChange={setZoomInfo} />
        ) : (
          <>
            <EventList
              events={events}
              typeLabels={typeLabels}
              onSelect={(e) => setSelectedEvent(e)}
            />
            <div className="flex-1 flex flex-col p-4 gap-4 overflow-y-auto">
              <StatsCards stats={stats} typeLabels={typeLabels} />
              <MainPanel
                selectedEvent={selectedEvent}
                zoomInfo={zoomInfo}
                onZoomChange={setZoomInfo}
                typeLabels={typeLabels}
              />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
