import { BarChart2, Home, Settings, Shield, FileText, Activity, Video } from "lucide-react"
import { useHashLocation } from "../hooks/useHashLocation"

const NAV = [
  { path: "/",         icon: Home,      label: "대시보드" },
  { path: "/cameras",  icon: Video,     label: "카메라 뷰" },
  { path: "/events",   icon: Activity,  label: "실시간 이벤트" },
  { path: "/reports",  icon: FileText,  label: "보고서 생성" },
  { path: "/settings", icon: Settings,  label: "설정" },
]

interface Props { connected: boolean }

export default function Sidebar({ connected }: Props) {
  const [location, navigate] = useHashLocation()

  return (
    <aside
      style={{
        width: 220,
        minWidth: 220,
        background: 'rgba(3,8,22,0.95)',
        borderRight: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      {/* 로고 */}
      <div style={{ padding: '20px 18px 16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* 의료 십자 아이콘 */}
          <div style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, #0ea5e9, #22d3ee)',
            borderRadius: 9,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(34,211,238,0.35)',
            flexShrink: 0,
          }}>
            <div style={{ position: 'relative', width: 18, height: 18 }}>
              <div style={{ position: 'absolute', left: '50%', top: 0, transform: 'translateX(-50%)', width: 5, height: 18, background: '#fff', borderRadius: 2 }} />
              <div style={{ position: 'absolute', top: '50%', left: 0, transform: 'translateY(-50%)', width: 18, height: 5, background: '#fff', borderRadius: 2 }} />
            </div>
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#e2eeff', lineHeight: 1.2 }}>Medicerti</div>
            <div style={{ fontSize: 11, color: '#22d3ee', fontWeight: 600, letterSpacing: '0.05em' }}>VISION</div>
          </div>
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: '#334155', letterSpacing: '0.04em' }}>
          병원 안전 AI 모니터링
        </div>
      </div>

      {/* 네비게이션 */}
      <nav style={{ padding: '12px 10px', flex: 1 }}>
        <div className="section-label" style={{ padding: '4px 8px 8px' }}>메뉴</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV.map(({ path, icon: Icon, label }) => {
            const active = location === path || (path !== "/" && location.startsWith(path))
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className={`nav-item ${active ? 'active' : ''}`}
                style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                <Icon size={15} />
                {label}
              </button>
            )
          })}
        </div>

        <div className="section-label" style={{ padding: '20px 8px 8px' }}>분석</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <button
            onClick={() => navigate("/events")}
            className="nav-item"
            style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <BarChart2 size={15} />
            이벤트 분석
          </button>
          <button
            onClick={() => navigate("/settings")}
            className="nav-item"
            style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <Shield size={15} />
            출입 관리
          </button>
        </div>
      </nav>

      {/* 하단 상태 */}
      <div style={{
        padding: '14px 14px',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            className="live-dot"
            style={{ background: connected ? '#4ade80' : '#ef4444' }}
          />
          <span style={{ fontSize: 12, color: connected ? '#4ade80' : '#ef4444', fontWeight: 600 }}>
            {connected ? 'AI 엔진 연결됨' : '연결 끊김'}
          </span>
        </div>
        <div style={{ fontSize: 11, color: '#1e293b', display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#334155' }}>v0.1.0</span>
          <span style={{ color: '#334155' }}>Edge AI</span>
        </div>
      </div>
    </aside>
  )
}
