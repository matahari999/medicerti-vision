import { Bell, RefreshCw, Wifi, WifiOff } from "lucide-react"
import { useClock, formatDate, formatTime } from "../hooks/useClock"
import { useHashLocation } from "../hooks/useHashLocation"
import { useAppDispatch } from "../context/AppContext"

const PAGE_TITLES: Record<string, { title: string; sub: string }> = {
  "/":         { title: "실시간 모니터링 대시보드", sub: "환자 안전 AI 실시간 감시 시스템" },
  "/events":   { title: "이벤트 로그",             sub: "감지된 이상 행동 전체 기록" },
  "/reports":  { title: "보고서 생성",             sub: "인증평가 서식 PDF 자동 생성" },
  "/settings": { title: "시스템 설정",             sub: "알림·카메라·구역 설정 관리" },
}

interface Props { connected: boolean }

export default function Header({ connected }: Props) {
  const now = useClock()
  const [location] = useHashLocation()
  const dispatch = useAppDispatch()

  const page = PAGE_TITLES[location] ?? PAGE_TITLES["/"]

  return (
    <header style={{
      height: 62,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
      background: 'rgba(2,8,23,0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 40,
    }}>
      {/* 왼쪽: 페이지 타이틀 */}
      <div>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#e2eeff' }}>{page.title}</div>
        <div style={{ fontSize: 11, color: '#334155', marginTop: 1 }}>{page.sub}</div>
      </div>

      {/* 오른쪽: 상태 + 시계 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {/* 날짜/시간 */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#e2eeff', fontFamily: 'monospace', letterSpacing: '0.05em' }}>
            {formatTime(now)}
          </div>
          <div style={{ fontSize: 10, color: '#475569', marginTop: 0 }}>{formatDate(now)} KST</div>
        </div>

        <div style={{ width: 1, height: 28, background: 'rgba(255,255,255,0.06)' }} />

        {/* 연결 상태 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 7,
          padding: '5px 12px',
          borderRadius: 20,
          background: connected ? 'rgba(74,222,128,0.08)' : 'rgba(239,68,68,0.08)',
          border: `1px solid ${connected ? 'rgba(74,222,128,0.2)' : 'rgba(239,68,68,0.2)'}`,
        }}>
          {connected
            ? <Wifi size={13} color="#4ade80" />
            : <WifiOff size={13} color="#f87171" />
          }
          <span style={{ fontSize: 12, fontWeight: 600, color: connected ? '#4ade80' : '#f87171' }}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        {/* 알림 버튼 */}
        <button
          style={{
            width: 34, height: 34,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderRadius: 9,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.07)',
            color: '#64748b',
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => {
            const el = e.currentTarget as HTMLButtonElement
            el.style.color = '#e2eeff'
            el.style.background = 'rgba(255,255,255,0.08)'
          }}
          onMouseLeave={e => {
            const el = e.currentTarget as HTMLButtonElement
            el.style.color = '#64748b'
            el.style.background = 'rgba(255,255,255,0.04)'
          }}
          title="알림"
        >
          <Bell size={15} />
        </button>

        {/* 이벤트 초기화 */}
        <button
          onClick={() => dispatch({ type: 'CLEAR_EVENTS' })}
          className="btn-ghost"
          style={{ padding: '5px 12px', fontSize: 12 }}
          title="이벤트 초기화"
        >
          <RefreshCw size={13} />
          초기화
        </button>
      </div>
    </header>
  )
}
