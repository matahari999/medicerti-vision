import { useState, useMemo } from "react"
import { useAppState } from "../context/AppContext"
import { AlertTriangle, Activity, Eye, UserX, Filter, Download } from "lucide-react"
import { EVENT_LABELS, EVENT_COLORS } from "../types"
import type { DetectionEvent } from "../types"

const ALL_TYPES = ['all', 'fall', 'elopement', 'loitering', 'stranger'] as const
const TYPE_ICONS = { fall: AlertTriangle, elopement: Activity, loitering: Eye, stranger: UserX }

function formatTs(ts: string) {
  try {
    return new Date(ts).toLocaleString('ko-KR', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    })
  } catch { return ts }
}

export default function EventsPage() {
  const { events } = useAppState()
  const [filter, setFilter] = useState<typeof ALL_TYPES[number]>('all')
  const [selected, setSelected] = useState<DetectionEvent | null>(null)

  const filtered = useMemo(() =>
    filter === 'all' ? events : events.filter(e => e.event_type === filter),
    [events, filter]
  )

  const exportCSV = () => {
    const header = 'timestamp,camera_id,event_type,confidence'
    const rows = filtered.map(e =>
      [e.timestamp, e.camera_id, e.event_type, e.confidence.toFixed(3)].join(',')
    )
    const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `medicerti_events_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-enter" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16, height: 'calc(100vh - 62px)', overflow: 'hidden' }}>

      {/* 툴바 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        {/* 필터 탭 */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginRight: 4 }}>
            <Filter size={13} color="#475569" />
            <span style={{ fontSize: 12, color: '#475569' }}>필터</span>
          </div>
          {ALL_TYPES.map(t => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`tab-btn ${filter === t ? 'active' : ''}`}
            >
              {t === 'all' ? '전체' : EVENT_LABELS[t]}
              <span style={{
                fontSize: 10, fontWeight: 700,
                padding: '1px 6px', borderRadius: 100,
                background: filter === t ? 'rgba(34,211,238,0.15)' : 'rgba(255,255,255,0.05)',
                color: filter === t ? '#22d3ee' : '#334155',
              }}>
                {t === 'all' ? events.length : events.filter(e => e.event_type === t).length}
              </span>
            </button>
          ))}
        </div>

        <button onClick={exportCSV} className="btn-ghost" style={{ fontSize: 12 }}>
          <Download size={13} />
          CSV 내보내기
        </button>
      </div>

      {/* 테이블 + 사이드 패널 */}
      <div style={{ display: 'flex', gap: 14, flex: 1, overflow: 'hidden', minHeight: 0 }}>

        {/* 이벤트 테이블 */}
        <div className="glass" style={{ flex: 1, borderRadius: 16, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {/* 헤더 */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '160px 100px 130px 90px 1fr',
            gap: 12,
            padding: '11px 20px',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            fontSize: 11,
            fontWeight: 700,
            color: '#334155',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
          }}>
            <span>감지 시각</span>
            <span>카메라</span>
            <span>이벤트 유형</span>
            <span>신뢰도</span>
            <span>신뢰도 바</span>
          </div>

          {/* 행 목록 */}
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {filtered.length === 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 200, gap: 8 }}>
                <span style={{ fontSize: 32 }}>📋</span>
                <span style={{ fontSize: 13, color: '#1e293b' }}>이벤트가 없습니다</span>
              </div>
            ) : (
              filtered.map((e, i) => {
                const c = EVENT_COLORS[e.event_type] ?? EVENT_COLORS.stranger
                const Icon = TYPE_ICONS[e.event_type as keyof typeof TYPE_ICONS] ?? Activity
                const isSelected = selected?.id === e.id

                return (
                  <div
                    key={e.id ?? i}
                    onClick={() => setSelected(isSelected ? null : e)}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '160px 100px 130px 90px 1fr',
                      gap: 12,
                      padding: '10px 20px',
                      borderBottom: '1px solid rgba(255,255,255,0.02)',
                      background: isSelected ? c.bg : i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                      cursor: 'pointer',
                      transition: 'background 0.1s',
                      alignItems: 'center',
                    }}
                    onMouseEnter={ev => { if (!isSelected) (ev.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.025)' }}
                    onMouseLeave={ev => { if (!isSelected) (ev.currentTarget as HTMLDivElement).style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}
                  >
                    <span style={{ fontSize: 12, color: '#64748b', fontFamily: 'monospace' }}>{formatTs(e.timestamp)}</span>
                    <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>{e.camera_id}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                      <div style={{
                        width: 22, height: 22, borderRadius: 6,
                        background: c.bg,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <Icon size={12} color={c.text} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: c.text }}>
                        {EVENT_LABELS[e.event_type] ?? e.event_type}
                      </span>
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#94a3b8', fontFamily: 'monospace' }}>
                      {(e.confidence * 100).toFixed(1)}%
                    </span>
                    <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${(e.confidence * 100).toFixed(0)}%`, background: c.text, borderRadius: 2, opacity: 0.7 }} />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* 우측 상세 패널 */}
        {selected && (
          <div className="glass card-enter" style={{ width: 260, borderRadius: 16, padding: 18, display: 'flex', flexDirection: 'column', gap: 14, flexShrink: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em' }}>이벤트 상세</div>

            {typeof selected.details?.snapshot_b64 === 'string' ? (
              <img
                src={`data:image/jpeg;base64,${selected.details.snapshot_b64}`}
                alt="snapshot"
                style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(255,255,255,0.08)' }}
              />
            ) : (
              <div style={{
                height: 130, borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.04)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, color: '#1e293b',
              }}>
                스냅샷 없음
              </div>
            )}

            {[
              { label: '이벤트 유형', value: EVENT_LABELS[selected.event_type] ?? selected.event_type },
              { label: '카메라',      value: selected.camera_id },
              { label: '신뢰도',      value: `${(selected.confidence * 100).toFixed(1)}%` },
              { label: '감지 시각',   value: new Date(selected.timestamp).toLocaleString('ko-KR') },
            ].map(({ label, value }) => (
              <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <span style={{ fontSize: 10, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8' }}>{value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
