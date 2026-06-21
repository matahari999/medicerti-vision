export interface AlertMessage {
  type: string
  camera_id: string
  event_type: string
  confidence: number
  timestamp: string
  snapshot_b64?: string
}

export interface DetectionEvent {
  id?: number
  timestamp: string
  camera_id: string
  event_type: string
  confidence: number
  snapshot_path?: string
  details: Record<string, unknown>
}

export interface EventStats {
  fall: number
  elopement: number
  loitering: number
  stranger: number
}

export interface ZoomInfo {
  active: boolean
  zoom_factor: number
  center: [number, number] | null
}

export interface TelegramConfig {
  enabled: boolean
  bot_token: string
  chat_id: string
  alert_types: string[]
}

export interface WhitelistEntry {
  id: number
  name: string
  role: string
  registered_at: string
}

export interface ReportResult {
  pdf_path: string
}

export interface Toast {
  id: number
  title: string
  message?: string
  type: 'success' | 'error' | 'warning' | 'info' | 'alert'
  duration?: number
}

export const EVENT_LABELS: Record<string, string> = {
  fall: '낙상',
  elopement: '이탈',
  loitering: '배회',
  stranger: '미등록 외부인',
}

export const EVENT_COLORS: Record<string, { text: string; border: string; bg: string; dot: string }> = {
  fall:      { text: '#f87171', border: 'rgba(248,113,113,0.3)', bg: 'rgba(248,113,113,0.08)', dot: '#f87171' },
  elopement: { text: '#fb923c', border: 'rgba(251,146,60,0.3)',  bg: 'rgba(251,146,60,0.08)',  dot: '#fb923c' },
  loitering: { text: '#fbbf24', border: 'rgba(251,191,36,0.3)',  bg: 'rgba(251,191,36,0.08)',  dot: '#fbbf24' },
  stranger:  { text: '#c084fc', border: 'rgba(192,132,252,0.3)', bg: 'rgba(192,132,252,0.08)', dot: '#c084fc' },
}
