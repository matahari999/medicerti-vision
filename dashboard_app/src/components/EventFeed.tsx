import { useEffect, useRef } from "react"
import { AlertTriangle, Activity, Eye, UserX, Inbox } from "lucide-react"
import type { DetectionEvent } from "../types"
import { EVENT_LABELS, EVENT_COLORS } from "../types"

const TYPE_ICONS = {
  fall:      AlertTriangle,
  elopement: Activity,
  loitering: Eye,
  stranger:  UserX,
}

function formatTs(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch { return ts }
}

interface Props {
  events: DetectionEvent[]
  onSelect?: (e: DetectionEvent) => void
  selected?: DetectionEvent | null
  maxHeight?: number
  compact?: boolean
}

export default function EventFeed({ events, onSelect, selected, maxHeight = 420, compact = false }: Props) {
  const topRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    topRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }, [events.length])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 헤더 */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: compact ? '10px 14px' : '14px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {events.length > 0 && (
            <div className="live-dot" style={{ background: '#22d3ee' }} />
          )}
          <span style={{ fontSize: 12, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            이벤트 피드
          </span>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 700,
          padding: '2px 8px', borderRadius: 100,
          background: events.length > 0 ? 'rgba(34,211,238,0.1)' : 'rgba(255,255,255,0.04)',
          color: events.length > 0 ? '#22d3ee' : '#334155',
          border: `1px solid ${events.length > 0 ? 'rgba(34,211,238,0.2)' : 'rgba(255,255,255,0.05)'}`,
        }}>
          {events.length}건
        </span>
      </div>

      {/* 목록 */}
      <div
        ref={topRef}
        style={{ overflowY: 'auto', maxHeight: compact ? undefined : maxHeight, flex: 1, padding: compact ? '6px' : '8px' }}
      >
        {events.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', gap: 12 }}>
            <Inbox size={32} color="#1e293b" />
            <div style={{ fontSize: 13, color: '#1e293b', textAlign: 'center' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>이벤트 없음</div>
              <div style={{ fontSize: 11, color: '#0f172a' }}>카메라 연결 시 이벤트가 표시됩니다</div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {events.map((e, i) => {
              const c = EVENT_COLORS[e.event_type] ?? EVENT_COLORS.stranger
              const Icon = TYPE_ICONS[e.event_type as keyof typeof TYPE_ICONS] ?? Activity
              const isSelected = selected?.id === e.id
              const isNew = i === 0

              return (
                <div
                  key={e.id}
                  className={isNew ? 'event-enter' : ''}
                  onClick={() => onSelect?.(e)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: compact ? '7px 10px' : '10px 12px',
                    borderRadius: 10,
                    borderLeft: `3px solid ${isSelected ? c.text : c.border}`,
                    background: isSelected ? c.bg : 'rgba(255,255,255,0.015)',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    border: `1px solid ${isSelected ? c.border : 'rgba(255,255,255,0.03)'}`,
                    borderLeftColor: isSelected ? c.text : c.border,
                    borderLeftWidth: 3,
                  }}
                  onMouseEnter={e2 => {
                    const el = e2.currentTarget as HTMLDivElement
                    if (!isSelected) { el.style.background = 'rgba(255,255,255,0.03)' }
                  }}
                  onMouseLeave={e2 => {
                    const el = e2.currentTarget as HTMLDivElement
                    if (!isSelected) { el.style.background = 'rgba(255,255,255,0.015)' }
                  }}
                >
                  {/* 아이콘 */}
                  <div style={{
                    width: 28, height: 28,
                    borderRadius: 7,
                    background: c.bg,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <Icon size={14} color={c.text} />
                  </div>

                  {/* 내용 */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: c.text }}>
                        {EVENT_LABELS[e.event_type] ?? e.event_type}
                      </span>
                      <span style={{ fontSize: 10, color: '#334155', flexShrink: 0 }}>
                        {formatTs(e.timestamp)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 3 }}>
                      <span style={{ fontSize: 11, color: '#475569' }}>{e.camera_id}</span>
                      {/* 신뢰도 바 */}
                      <div style={{ flex: 1, height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${(e.confidence * 100).toFixed(0)}%`,
                          background: c.text,
                          borderRadius: 2,
                          opacity: 0.7,
                        }} />
                      </div>
                      <span style={{ fontSize: 10, color: '#475569', flexShrink: 0 }}>
                        {(e.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
