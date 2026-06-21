import { useEffect, useRef, useState } from "react"
import { Activity, AlertTriangle, Eye, UserX } from "lucide-react"
import type { EventStats } from "../types"

const CARD_CONFIG = {
  fall: {
    label: '낙상',
    sub: '환자 낙상 감지',
    Icon: AlertTriangle,
    color: '#f87171',
    glow: 'rgba(248,113,113,0.25)',
    bg: 'rgba(248,113,113,0.06)',
    border: 'rgba(248,113,113,0.15)',
    topLine: 'linear-gradient(90deg, transparent, #f87171, transparent)',
  },
  elopement: {
    label: '이탈',
    sub: '구역 이탈 감지',
    Icon: Activity,
    color: '#fb923c',
    glow: 'rgba(251,146,60,0.25)',
    bg: 'rgba(251,146,60,0.06)',
    border: 'rgba(251,146,60,0.15)',
    topLine: 'linear-gradient(90deg, transparent, #fb923c, transparent)',
  },
  loitering: {
    label: '배회',
    sub: '장시간 배회 감지',
    Icon: Eye,
    color: '#fbbf24',
    glow: 'rgba(251,191,36,0.25)',
    bg: 'rgba(251,191,36,0.06)',
    border: 'rgba(251,191,36,0.15)',
    topLine: 'linear-gradient(90deg, transparent, #fbbf24, transparent)',
  },
  stranger: {
    label: '미등록 외부인',
    sub: '미등록 인원 감지',
    Icon: UserX,
    color: '#c084fc',
    glow: 'rgba(192,132,252,0.25)',
    bg: 'rgba(192,132,252,0.06)',
    border: 'rgba(192,132,252,0.15)',
    topLine: 'linear-gradient(90deg, transparent, #c084fc, transparent)',
  },
}

function useCountUp(target: number) {
  const [count, setCount] = useState(0)
  const prevRef = useRef(0)

  useEffect(() => {
    const start = prevRef.current
    const diff = target - start
    if (diff === 0) return
    const duration = Math.min(600, Math.max(200, Math.abs(diff) * 40))
    const startTime = performance.now()

    const animate = (now: number) => {
      const p = Math.min((now - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setCount(Math.round(start + diff * eased))
      if (p < 1) requestAnimationFrame(animate)
      else prevRef.current = target
    }
    requestAnimationFrame(animate)
  }, [target])

  return count
}

interface Props {
  type: keyof EventStats
  value: number
}

export default function StatCard({ type, value }: Props) {
  const cfg = CARD_CONFIG[type]
  const count = useCountUp(value)
  const [hovered, setHovered] = useState(false)
  const { Icon } = cfg

  return (
    <div
      className="card-enter"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: 'relative',
        overflow: 'hidden',
        padding: '20px 22px',
        borderRadius: 16,
        border: `1px solid ${hovered ? cfg.border : 'rgba(255,255,255,0.05)'}`,
        background: hovered ? cfg.bg : 'rgba(10,20,45,0.5)',
        transition: 'all 0.25s ease',
        transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
        boxShadow: hovered ? `0 8px 32px rgba(0,0,0,0.4), 0 0 20px ${cfg.glow}` : 'none',
        cursor: 'default',
      }}
    >
      {/* 상단 라인 */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 1,
        background: hovered ? cfg.topLine : 'transparent',
        transition: 'background 0.25s',
      }} />

      {/* 배경 글로우 */}
      <div style={{
        position: 'absolute', top: -20, right: -20,
        width: 80, height: 80,
        borderRadius: '50%',
        background: cfg.glow,
        filter: 'blur(30px)',
        opacity: hovered ? 0.6 : 0.3,
        transition: 'opacity 0.25s',
        pointerEvents: 'none',
      }} />

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: '#475569', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>
            {cfg.sub}
          </div>
          <div style={{ fontSize: 40, fontWeight: 800, color: hovered ? cfg.color : '#e2eeff', lineHeight: 1, transition: 'color 0.25s', fontVariantNumeric: 'tabular-nums' }}>
            {count}
          </div>
          <div style={{ marginTop: 6, fontSize: 13, fontWeight: 700, color: cfg.color }}>
            {cfg.label}
          </div>
        </div>

        {/* 아이콘 */}
        <div style={{
          width: 42, height: 42,
          borderRadius: 11,
          background: `rgba(${type === 'fall' ? '248,113,113' : type === 'elopement' ? '251,146,60' : type === 'loitering' ? '251,191,36' : '192,132,252'},0.12)`,
          border: `1px solid ${cfg.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: hovered ? `0 0 16px ${cfg.glow}` : 'none',
          transition: 'box-shadow 0.25s',
        }}>
          <Icon size={18} color={cfg.color} />
        </div>
      </div>

      {/* 하단: 오늘 통계 */}
      <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.04)', display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 11, color: '#334155' }}>현재 세션</span>
        <span style={{
          fontSize: 11, fontWeight: 700,
          color: value > 0 ? cfg.color : '#1e293b',
          padding: '1px 7px',
          borderRadius: 100,
          background: value > 0 ? cfg.bg : 'transparent',
          border: `1px solid ${value > 0 ? cfg.border : 'transparent'}`,
        }}>
          {value > 0 ? `+${value} 건` : '이상 없음'}
        </span>
      </div>
    </div>
  )
}
