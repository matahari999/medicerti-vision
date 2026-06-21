import { AlertTriangle, CheckCircle, Info, X, XCircle, Zap } from "lucide-react"
import type { Toast as ToastType } from "../types"

const ICONS = {
  success: CheckCircle,
  error:   XCircle,
  warning: AlertTriangle,
  info:    Info,
  alert:   Zap,
}

const COLORS = {
  success: { bg: 'rgba(74,222,128,0.1)',  border: 'rgba(74,222,128,0.25)',  icon: '#4ade80' },
  error:   { bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.25)', icon: '#f87171' },
  warning: { bg: 'rgba(251,191,36,0.1)',  border: 'rgba(251,191,36,0.25)',  icon: '#fbbf24' },
  info:    { bg: 'rgba(34,211,238,0.08)', border: 'rgba(34,211,238,0.2)',   icon: '#22d3ee' },
  alert:   { bg: 'rgba(192,132,252,0.1)', border: 'rgba(192,132,252,0.25)', icon: '#c084fc' },
}

interface Props {
  toasts: ToastType[]
  onDismiss: (id: number) => void
}

export default function ToastContainer({ toasts, onDismiss }: Props) {
  return (
    <div style={{
      position: 'fixed',
      bottom: 24,
      right: 24,
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      pointerEvents: 'none',
    }}>
      {toasts.map(t => {
        const Icon = ICONS[t.type]
        const c = COLORS[t.type]
        return (
          <div
            key={t.id}
            className="toast-enter"
            style={{
              pointerEvents: 'auto',
              minWidth: 280,
              maxWidth: 380,
              background: 'rgba(8,15,35,0.95)',
              border: `1px solid ${c.border}`,
              borderRadius: 12,
              padding: '12px 14px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
              backdropFilter: 'blur(20px)',
              boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px ${c.border}`,
            }}
          >
            <div style={{
              width: 32, height: 32,
              borderRadius: 8,
              background: c.bg,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <Icon size={16} color={c.icon} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#e2eeff', marginBottom: 2 }}>{t.title}</div>
              {t.message && (
                <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.4 }}>{t.message}</div>
              )}
            </div>
            <button
              onClick={() => onDismiss(t.id)}
              style={{
                flexShrink: 0,
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#475569', padding: 2,
                display: 'flex', alignItems: 'center',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = '#94a3b8')}
              onMouseLeave={e => (e.currentTarget.style.color = '#475569')}
            >
              <X size={14} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
