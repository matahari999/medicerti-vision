import { useMemo } from "react"
import type { DetectionEvent } from "../types"

const TYPE_COLORS: Record<string, string> = {
  fall:      '#f87171',
  elopement: '#fb923c',
  loitering: '#fbbf24',
  stranger:  '#c084fc',
}
const TYPES = ['fall', 'elopement', 'loitering', 'stranger']
const BINS = 30

interface Props {
  events: DetectionEvent[]
}

export default function ActivityChart({ events }: Props) {
  const bins = useMemo(() => {
    const now = Date.now()
    return Array.from({ length: BINS }, (_, i) => {
      const windowStart = now - (BINS - i) * 60_000
      const windowEnd   = now - (BINS - i - 1) * 60_000
      const bucket: Record<string, number> = {}
      for (const t of TYPES) bucket[t] = 0
      for (const ev of events) {
        const ts = new Date(ev.timestamp).getTime()
        if (ts >= windowStart && ts < windowEnd && bucket[ev.event_type] !== undefined) {
          bucket[ev.event_type]++
        }
      }
      return bucket
    })
  }, [events])

  const maxVal = useMemo(() => {
    return Math.max(1, ...bins.map(b => Object.values(b).reduce((a, v) => a + v, 0)))
  }, [bins])

  const W = 600
  const H = 72
  const barW = Math.floor((W - (BINS - 1) * 3) / BINS)
  const gap = 3

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            이벤트 빈도 추이
          </span>
          <span style={{ fontSize: 11, color: '#1e293b' }}>최근 30분</span>
        </div>
        {/* 범례 */}
        <div style={{ display: 'flex', gap: 14 }}>
          {TYPES.map(t => (
            <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: TYPE_COLORS[t] }} />
              <span style={{ fontSize: 10, color: '#334155' }}>
                {{ fall: '낙상', elopement: '이탈', loitering: '배회', stranger: '미등록' }[t]}
              </span>
            </div>
          ))}
        </div>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: '100%', height: H, display: 'block' }}
        preserveAspectRatio="none"
      >
        {/* 그리드 라인 */}
        {[0.25, 0.5, 0.75, 1].map(f => (
          <line
            key={f}
            x1={0} y1={H - H * f} x2={W} y2={H - H * f}
            stroke="rgba(255,255,255,0.04)" strokeWidth={1}
          />
        ))}

        {bins.map((bin, i) => {
          const x = i * (barW + gap)
          let yOffset = H
          return (
            <g key={i}>
              {TYPES.map(t => {
                const val = bin[t]
                if (!val) return null
                const barH = Math.max(2, (val / maxVal) * H)
                yOffset -= barH
                return (
                  <rect
                    key={t}
                    x={x}
                    y={yOffset}
                    width={barW}
                    height={barH}
                    fill={TYPE_COLORS[t]}
                    opacity={0.75}
                    rx={1}
                  />
                )
              })}
            </g>
          )
        })}

        {/* 현재 시간 표시선 */}
        <line
          x1={W - barW - gap} y1={0} x2={W - barW - gap} y2={H}
          stroke="rgba(34,211,238,0.3)" strokeWidth={1} strokeDasharray="3,3"
        />
      </svg>

      {/* X축 레이블 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
        <span style={{ fontSize: 10, color: '#1e293b' }}>30분 전</span>
        <span style={{ fontSize: 10, color: '#1e293b' }}>15분 전</span>
        <span style={{ fontSize: 10, color: '#22d3ee' }}>지금</span>
      </div>
    </div>
  )
}
