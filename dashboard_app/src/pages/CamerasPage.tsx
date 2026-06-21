import { useEffect, useState, useCallback } from "react"
import { VideoOff, RefreshCw, Maximize2, X } from "lucide-react"
import { useAppState } from "../context/AppContext"
import { API_BASE } from "../lib/utils"
import { EVENT_LABELS, EVENT_COLORS } from "../types"
import type { DetectionEvent } from "../types"

interface Camera {
  id: string
  label: string
  rtsp_url: string
  streaming: boolean
}

const DEMO_CAMERAS: Camera[] = [
  { id: "CAM-01", label: "병동 A 복도",    rtsp_url: "", streaming: false },
  { id: "CAM-02", label: "응급실 입구",    rtsp_url: "", streaming: false },
  { id: "CAM-03", label: "중환자실 앞",    rtsp_url: "", streaming: false },
  { id: "CAM-04", label: "엘리베이터 홀", rtsp_url: "", streaming: false },
]

function recentAlert(events: DetectionEvent[], cameraId: string) {
  const ev = events.find(e => e.camera_id === cameraId)
  if (!ev) return null
  if (Date.now() - new Date(ev.timestamp).getTime() > 60_000) return null
  return ev
}

/* ── 카메라 셀 ── */
function CameraCell({
  cam, events, onExpand,
}: {
  cam: Camera
  events: DetectionEvent[]
  onExpand: (id: string) => void
}) {
  const alert = recentAlert(events, cam.id)
  const c = alert ? EVENT_COLORS[alert.event_type] : null

  return (
    <div
      onClick={() => onExpand(cam.id)}
      style={{
        position: "relative",
        background: "#000",
        borderRadius: 12,
        overflow: "hidden",
        border: `1px solid ${c ? c.border : "rgba(255,255,255,0.06)"}`,
        aspectRatio: "16/9",
        cursor: "pointer",
        transition: "border-color 0.2s",
      }}
    >
      {/* 영상 or 오프라인 */}
      {cam.streaming ? (
        <img
          src={`${API_BASE}/cameras/${cam.id}/stream`}
          alt={cam.id}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          onError={e => { (e.target as HTMLImageElement).style.display = "none" }}
        />
      ) : (
        <div style={{
          width: "100%", height: "100%",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          background: "#050c1e", gap: 10,
        }}>
          <VideoOff size={32} color="#1e3050" />
          <span style={{ fontSize: 12, color: "#1e3050" }}>스트림 대기 중</span>
        </div>
      )}

      {/* 상단: 이름 + LIVE 배지 */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        padding: "10px 12px",
        background: "linear-gradient(to bottom, rgba(0,0,0,0.75), transparent)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        pointerEvents: "none",
      }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#e2eeff", letterSpacing: "0.02em" }}>
          {cam.label}
        </span>
        {cam.streaming && (
          <span style={{
            display: "flex", alignItems: "center", gap: 4,
            padding: "2px 7px", borderRadius: 5,
            background: "rgba(74,222,128,0.2)", border: "1px solid rgba(74,222,128,0.4)",
            fontSize: 9, fontWeight: 800, color: "#4ade80", letterSpacing: "0.06em",
          }}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#4ade80", display: "inline-block" }} />
            LIVE
          </span>
        )}
      </div>

      {/* 카메라 ID */}
      <div style={{
        position: "absolute", bottom: alert ? 36 : 8, left: 12,
        fontSize: 10, fontWeight: 700, color: "rgba(255,255,255,0.3)",
        letterSpacing: "0.06em", pointerEvents: "none",
      }}>
        {cam.id}
      </div>

      {/* 하단: 이벤트 알림 */}
      {alert && c && (
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          padding: "8px 12px",
          background: `linear-gradient(to top, rgba(0,0,0,0.85), transparent)`,
          display: "flex", alignItems: "center", gap: 8,
          pointerEvents: "none",
        }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: c.text, flexShrink: 0 }} />
          <span style={{ fontSize: 11, fontWeight: 700, color: c.text }}>
            {EVENT_LABELS[alert.event_type]} 감지
          </span>
          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginLeft: "auto" }}>
            {new Date(alert.timestamp).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
          </span>
        </div>
      )}

      {/* 확대 버튼 hover 시만 표시 */}
      <div style={{
        position: "absolute", top: 8, right: 8,
        opacity: 0,
        transition: "opacity 0.15s",
      }} className="cam-expand">
        <div style={{
          background: "rgba(0,0,0,0.6)", border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 7, padding: "5px 6px", color: "#e2eeff",
          display: "flex",
        }}>
          <Maximize2 size={12} />
        </div>
      </div>
    </div>
  )
}

/* ── 전체화면 뷰 ── */
function ExpandedView({ cam, events, onClose }: { cam: Camera; events: DetectionEvent[]; onClose: () => void }) {
  const alert = recentAlert(events, cam.id)
  const c = alert ? EVENT_COLORS[alert.event_type] : null

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 200,
      background: "rgba(2,8,23,0.97)",
      display: "flex", flexDirection: "column",
    }}>
      {/* 상단 바 */}
      <div style={{
        padding: "14px 20px",
        display: "flex", alignItems: "center", gap: 12,
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(6,14,35,0.8)",
      }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: "linear-gradient(135deg,#0ea5e9,#22d3ee)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 14, fontWeight: 900, color: "#fff",
        }}>✚</div>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#e2eeff" }}>{cam.label}</div>
          <div style={{ fontSize: 11, color: "#445568" }}>{cam.id} · {cam.rtsp_url || "로컬 스트림"}</div>
        </div>
        {cam.streaming && (
          <span style={{
            display: "flex", alignItems: "center", gap: 5,
            padding: "3px 10px", borderRadius: 6,
            background: "rgba(74,222,128,0.1)", border: "1px solid rgba(74,222,128,0.3)",
            fontSize: 11, fontWeight: 700, color: "#4ade80",
          }}>
            ● LIVE
          </span>
        )}
        {alert && c && (
          <span style={{
            padding: "3px 10px", borderRadius: 6,
            background: c.bg, border: `1px solid ${c.border}`,
            fontSize: 11, fontWeight: 700, color: c.text,
          }}>
            ⚠ {EVENT_LABELS[alert.event_type]} 감지됨
          </span>
        )}
        <button
          onClick={onClose}
          style={{
            marginLeft: "auto",
            background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8, padding: "6px 8px", cursor: "pointer", color: "#94a3b8",
            display: "flex",
          }}
        >
          <X size={16} />
        </button>
      </div>

      {/* 영상 */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
        {cam.streaming ? (
          <img
            src={`${API_BASE}/cameras/${cam.id}/stream`}
            alt={cam.id}
            style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", borderRadius: 12 }}
          />
        ) : (
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 16,
          }}>
            <VideoOff size={56} color="#1e3050" />
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#334155", marginBottom: 8 }}>
                카메라 스트림이 아직 시작되지 않았습니다
              </div>
              <div style={{ fontSize: 13, color: "#1e3050" }}>
                AI 파이프라인이 실행되면 여기에 실시간 영상이 표시됩니다
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── 메인 페이지 ── */
type GridMode = "1" | "2" | "3" | "4"

export default function CamerasPage() {
  const { events } = useAppState()
  const [cameras, setCameras] = useState<Camera[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [cols, setCols] = useState<GridMode>("2")

  const fetchCameras = useCallback(async () => {
    try {
      const [camRes, pipeRes] = await Promise.all([
        fetch(`${API_BASE}/cameras`),
        fetch(`${API_BASE}/pipeline/status`),
      ])

      const camData = camRes.ok ? await camRes.json() : null
      const pipeData = pipeRes.ok ? await pipeRes.json() : null

      let list: Camera[] = camData?.cameras ?? []

      // 파이프라인 상태에서 보완
      if (!list.length && pipeData?.cameras) {
        list = Object.entries(pipeData.cameras).map(([id, v]: any) => ({
          id,
          label: v.label || id,
          rtsp_url: v.rtsp_url || "",
          streaming: false,
        }))
      }

      // 카메라 미설정 시 데모 목록
      if (!list.length) list = DEMO_CAMERAS

      setCameras(list)
    } catch {
      setCameras(DEMO_CAMERAS)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCameras()
    const t = setInterval(fetchCameras, 5000)
    return () => clearInterval(t)
  }, [fetchCameras])

  // ESC로 전체화면 닫기
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") setExpanded(null) }
    window.addEventListener("keydown", h)
    return () => window.removeEventListener("keydown", h)
  }, [])

  const expandedCam = cameras.find(c => c.id === expanded)
  const activeCount = cameras.filter(c => c.streaming).length

  return (
    <>
      {/* 전체화면 오버레이 */}
      {expanded && expandedCam && (
        <ExpandedView cam={expandedCam} events={events} onClose={() => setExpanded(null)} />
      )}

      <div className="page-enter" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>

        {/* 헤더 */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#e2eeff" }}>카메라 모니터링</div>
            <div style={{ fontSize: 13, color: "#475569", marginTop: 3 }}>
              총 <strong style={{ color: "#94a3b8" }}>{cameras.length}</strong>대 연결 ·{" "}
              활성 <strong style={{ color: "#4ade80" }}>{activeCount}</strong>대
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {/* 그리드 레이아웃 */}
            {(["1", "2", "3", "4"] as GridMode[]).map(n => (
              <button
                key={n}
                onClick={() => setCols(n)}
                style={{
                  width: 34, height: 34, borderRadius: 8, fontSize: 12, fontWeight: 700,
                  cursor: "pointer", border: "1px solid",
                  borderColor: cols === n ? "rgba(34,211,238,0.4)" : "rgba(255,255,255,0.06)",
                  background: cols === n ? "rgba(34,211,238,0.08)" : "rgba(255,255,255,0.02)",
                  color: cols === n ? "#22d3ee" : "#475569",
                }}
              >
                {n}×{n}
              </button>
            ))}
            <button
              onClick={fetchCameras}
              title="새로고침"
              style={{
                width: 34, height: 34, borderRadius: 8, cursor: "pointer",
                border: "1px solid rgba(255,255,255,0.06)",
                background: "rgba(255,255,255,0.02)", color: "#475569",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        {/* 활성 이벤트 배너 */}
        {events.length > 0 && (() => {
          const latest = events[0]
          const c = EVENT_COLORS[latest.event_type]
          const age = Date.now() - new Date(latest.timestamp).getTime()
          if (age > 60_000) return null
          return (
            <div style={{
              padding: "10px 16px", borderRadius: 10,
              background: c.bg, border: `1px solid ${c.border}`,
              display: "flex", alignItems: "center", gap: 10,
              fontSize: 13,
            }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: c.text, flexShrink: 0 }} />
              <span style={{ color: c.text, fontWeight: 700 }}>
                {EVENT_LABELS[latest.event_type]} 감지됨
              </span>
              <span style={{ color: "rgba(255,255,255,0.5)" }}>
                {latest.camera_id} · 신뢰도 {(latest.confidence * 100).toFixed(0)}%
              </span>
              <span style={{ marginLeft: "auto", fontSize: 12, color: "rgba(255,255,255,0.35)" }}>
                {new Date(latest.timestamp).toLocaleTimeString("ko-KR")}
              </span>
            </div>
          )
        })()}

        {/* 카메라 그리드 */}
        {loading ? (
          <div style={{ textAlign: "center", padding: 80, color: "#334155", fontSize: 14 }}>
            카메라 목록 불러오는 중…
          </div>
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: `repeat(${cols}, 1fr)`,
            gap: 12,
          }}>
            {cameras.map(cam => (
              <CameraCell key={cam.id} cam={cam} events={events} onExpand={setExpanded} />
            ))}
          </div>
        )}

        {/* 파이프라인 미실행 안내 */}
        {!loading && cameras.every(c => !c.streaming) && (
          <div style={{
            padding: "16px 20px", borderRadius: 12,
            background: "rgba(34,211,238,0.03)", border: "1px solid rgba(34,211,238,0.08)",
            fontSize: 13, color: "#445568", textAlign: "center",
          }}>
            카메라 스트림이 없습니다. AI 파이프라인이 시작되면 영상이 자동으로 표시됩니다.
          </div>
        )}
      </div>

      <style>{`
        .cam-cell:hover .cam-expand { opacity: 1 !important; }
      `}</style>
    </>
  )
}
