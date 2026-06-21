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
