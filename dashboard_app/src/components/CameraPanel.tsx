import { useEffect, useState } from "react"
import { Camera, VideoOff, Wifi, WifiOff } from "lucide-react"
import type { DetectionEvent } from "../types"
import { EVENT_LABELS, EVENT_COLORS } from "../types"
import { API_BASE } from "../lib/utils"
import { useHashLocation } from "../hooks/useHashLocation"

const DEMO_CAMERAS = [
  { id: "CAM-01", label: "병동 A 복도" },
  { id: "CAM-02", label: "응급실 입구" },
  { id: "CAM-03", label: "중환자실 앞" },
  { id: "CAM-04", label: "엘리베이터 홀" },
]

interface CameraInfo { id: string; label: string; streaming: boolean }

interface Props { connected: boolean; events: DetectionEvent[] }

export default function CameraPanel({ connected, events }: Props) {
  const [, navigate] = useHashLocation()
  const [cameraList, setCameraList] = useState<CameraInfo[]>([])
  // snapshot URL: camera_id → objectURL (refreshed every 2s when streaming)
  const [thumbs, setThumbs] = useState<Record<string, string>>({})

  // 카메라 목록 가져오기
  useEffect(() => {
    async function fetchList() {
      try {
        const res = await fetch(`${API_BASE}/cameras`)
        if (!res.ok) throw new Error()
        const data = await res.json()
        if (data.cameras?.length) {
          setCameraList(data.cameras)
          return
        }
      } catch { /* fallthrough */ }
      setCameraList(DEMO_CAMERAS.map(c => ({ ...c, streaming: false })))
    }
    fetchList()
    const t = setInterval(fetchList, 5000)
    return () => clearInterval(t)
  }, [])

  // 스트리밍 중인 카메라만 스냅샷 폴링
  useEffect(() => {
    if (!connected) return
    const streaming = cameraList.filter(c => c.streaming)
    if (!streaming.length) return

    let alive = true
    async function poll() {
      while (alive) {
        const updates: Record<string, string> = {}
        await Promise.allSettled(
          streaming.map(async c => {
            try {
              const res = await fetch(`${API_BASE}/cameras/${c.id}/snapshot`, { cache: "no-store" })
              if (!res.ok) return
              const blob = await res.blob()
              updates[c.id] = URL.createObjectURL(blob)
            } catch { /* skip */ }
          })
        )
        if (alive) setThumbs(prev => {
          // revoke old object URLs to avoid memory leak
          Object.values(prev).forEach(u => URL.revokeObjectURL(u))
          return updates
        })
        await new Promise(r => setTimeout(r, 2000))
      }
    }
    poll()
    return () => { alive = false }
  }, [connected, cameraList])

  const lastEventByCamera = events.reduce<Record<string, DetectionEvent>>((acc, ev) => {
    if (!acc[ev.camera_id]) acc[ev.camera_id] = ev
    return acc
  }, {})

  const totalCams = cameraList.length
  const activeCams = cameraList.filter(c => c.streaming).length

  return (
    <div>
      {/* 헤더 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            카메라
          </span>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: "1px 7px", borderRadius: 100,
            background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.15)",
            color: "#4ade80",
          }}>
            {activeCams}/{totalCams} LIVE
          </span>
        </div>
        <button
          onClick={() => navigate("/cameras")}
          style={{
            fontSize: 11, color: "#22d3ee", background: "none", border: "none",
            cursor: "pointer", padding: "2px 8px",
            borderRadius: 6, transition: "background 0.15s",
          }}
        >
          전체 보기 →
        </button>
      </div>

      {/* 카메라 그리드 (2×2) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {cameraList.slice(0, 4).map(cam => {
          const ev = lastEventByCamera[cam.id] ?? null
          const c = ev ? (EVENT_COLORS[ev.event_type] ?? EVENT_COLORS.stranger) : null
          const hasAlert = ev && (Date.now() - new Date(ev.timestamp).getTime()) < 30_000
          const thumb = thumbs[cam.id]

          return (
            <div
              key={cam.id}
              onClick={() => navigate("/cameras")}
              style={{
                borderRadius: 12,
                border: `1px solid ${hasAlert ? c!.border : "rgba(255,255,255,0.05)"}`,
                overflow: "hidden",
                cursor: "pointer",
                background: "#000",
                transition: "border-color 0.2s",
              }}
            >
              {/* 영상 영역 */}
              <div style={{
                height: 76,
                background: "#050c1e",
                position: "relative",
                overflow: "hidden",
              }}>
                {/* 실제 스냅샷 or MJPEG (스트리밍 시) */}
                {cam.streaming ? (
                  <img
                    src={thumb || `${API_BASE}/cameras/${cam.id}/stream`}
                    alt={cam.id}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                ) : (
                  <div style={{
                    width: "100%", height: "100%",
                    display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center", gap: 5,
                    background: connected
                      ? "repeating-linear-gradient(0deg, transparent, transparent 4px, rgba(74,222,128,0.015) 4px, rgba(74,222,128,0.015) 5px)"
                      : "transparent",
                  }}>
                    <Camera size={20} color={connected ? "#4ade80" : "#1e293b"} />
                    <span style={{ fontSize: 9, fontWeight: 700, color: connected ? "#4ade80" : "#1e293b", letterSpacing: "0.08em" }}>
                      {connected ? "● 연결됨" : "○ OFFLINE"}
                    </span>
                  </div>
                )}

                {/* REC 배지 */}
                {cam.streaming && (
                  <div style={{
                    position: "absolute", top: 5, right: 5,
                    padding: "1px 5px", borderRadius: 4,
                    background: "rgba(239,68,68,0.85)", fontSize: 8, fontWeight: 800, color: "#fff",
                  }}>
                    ● REC
                  </div>
                )}

                {/* 이벤트 오버레이 */}
                {hasAlert && c && (
                  <div style={{
                    position: "absolute", bottom: 0, left: 0, right: 0,
                    padding: "4px 8px",
                    background: `linear-gradient(to top, rgba(0,0,0,0.8), transparent)`,
                  }}>
                    <span style={{ fontSize: 9, fontWeight: 700, color: c.text }}>
                      ⚠ {EVENT_LABELS[ev!.event_type]}
                    </span>
                  </div>
                )}
              </div>

              {/* 정보 바 */}
              <div style={{ padding: "7px 10px", background: "rgba(5,12,30,0.9)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8" }}>{cam.id}</span>
                  {cam.streaming
                    ? <Wifi size={10} color="#4ade80" />
                    : <WifiOff size={10} color="#334155" />}
                </div>
                <div style={{ fontSize: 10, color: "#475569", marginTop: 1 }}>{cam.label}</div>
              </div>
            </div>
          )
        })}
      </div>

      {/* 카메라 더 있을 때 */}
      {cameraList.length > 4 && (
        <button
          onClick={() => navigate("/cameras")}
          style={{
            width: "100%", marginTop: 10, padding: "8px 0",
            borderRadius: 8, background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.05)",
            color: "#475569", fontSize: 12, cursor: "pointer",
          }}
        >
          +{cameraList.length - 4}대 더 보기
        </button>
      )}
    </div>
  )
}
