import { useEffect, useState } from "react"
import { Bell, Camera, Users, MapPin, Save, Send, Trash2, ZoomIn, ZoomOut, Plus } from "lucide-react"
import type { TelegramConfig, WhitelistEntry, ZoomInfo } from "../types"
import { apiPost, apiGet } from "../lib/utils"
import { useToast } from "../hooks/useToast"

const TABS = [
  { key: 'telegram',   icon: Bell,   label: 'Telegram 알림' },
  { key: 'zoom',       icon: Camera, label: '디지털 줌' },
  { key: 'whitelist',  icon: Users,  label: '출입 관리' },
  { key: 'geo',        icon: MapPin, label: 'GeoFence' },
]

const EVENT_OPTIONS = [
  { key: 'fall',      label: '낙상' },
  { key: 'elopement', label: '이탈' },
  { key: 'loitering', label: '배회' },
  { key: 'stranger',  label: '미등록' },
]

export default function SettingsPage() {
  const [tab, setTab] = useState('telegram')
  const { toast } = useToast()

  /* ─── Telegram ─── */
  const [telegram, setTelegram] = useState<TelegramConfig>({
    enabled: false, bot_token: '', chat_id: '', alert_types: ['fall'],
  })
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  /* ─── Zoom ─── */
  const [zoom, setZoom] = useState<ZoomInfo>({ active: false, zoom_factor: 2.0, center: null })

  /* ─── Whitelist ─── */
  const [whitelist, setWhitelist] = useState<WhitelistEntry[]>([])
  const [newName, setNewName] = useState('')
  const [newRole, setNewRole] = useState('')

  useEffect(() => {
    apiGet<TelegramConfig>('/notify/config').then(setTelegram).catch(() => {})
    apiGet<WhitelistEntry[]>('/faces/whitelist').then(setWhitelist).catch(() => {})
    apiGet<ZoomInfo>('/zoom').then(setZoom).catch(() => {})
  }, [])

  const saveTelegram = async () => {
    setSaving(true)
    try {
      await apiPost('/notify/config', telegram)
      toast('저장 완료', { type: 'success', message: 'Telegram 설정이 저장되었습니다.' })
    } catch {
      toast('저장 실패', { type: 'error' })
    } finally { setSaving(false) }
  }

  const testTelegram = async () => {
    setTesting(true)
    try {
      await apiPost('/notify/telegram/test', {})
      toast('테스트 메시지 발송', { type: 'success' })
    } catch {
      toast('발송 실패', { type: 'error', message: 'Bot Token / Chat ID를 확인하세요.' })
    } finally { setTesting(false) }
  }

  const removeFace = async (name: string) => {
    try {
      await apiPost('/faces/remove', { name })
      setWhitelist(prev => prev.filter(w => w.name !== name))
      toast('삭제 완료', { type: 'success', message: `${name} 삭제됨` })
    } catch {
      toast('삭제 실패', { type: 'error' })
    }
  }

  const handleZoomFactor = async (f: number) => {
    const clamped = Math.max(1, Math.min(8, f))
    setZoom(prev => ({ ...prev, zoom_factor: clamped }))
    try { await apiPost('/zoom/factor', { factor: clamped }) } catch { /* ignore */ }
  }

  return (
    <div className="page-enter" style={{ padding: 24, display: 'flex', gap: 20, height: 'calc(100vh - 62px)', overflow: 'hidden' }}>

      {/* 탭 사이드바 */}
      <div className="glass" style={{ width: 200, borderRadius: 16, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0, alignSelf: 'flex-start' }}>
        <div className="section-label" style={{ padding: '4px 10px 8px' }}>설정 메뉴</div>
        {TABS.map(t => {
          const { icon: Icon } = t
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`tab-btn ${tab === t.key ? 'active' : ''}`}
              style={{ width: '100%', textAlign: 'left', padding: '9px 12px' }}
            >
              <Icon size={14} />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* 설정 콘텐츠 */}
      <div className="glass" style={{ flex: 1, borderRadius: 16, padding: '24px 28px', overflowY: 'auto' }}>

        {/* ─── Telegram ─── */}
        {tab === 'telegram' && (
          <div style={{ maxWidth: 560 }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: '#e2eeff', marginBottom: 4, marginTop: 0 }}>Telegram 알림 설정</h2>
            <p style={{ fontSize: 13, color: '#475569', marginBottom: 24, marginTop: 0 }}>
              이벤트 발생 시 Telegram Bot을 통해 즉시 알림과 스냅샷을 수신합니다.
            </p>

            {/* 활성화 토글 */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', borderRadius: 12, background: telegram.enabled ? 'rgba(34,211,238,0.05)' : 'rgba(255,255,255,0.02)', border: `1px solid ${telegram.enabled ? 'rgba(34,211,238,0.15)' : 'rgba(255,255,255,0.05)'}`, marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#e2eeff' }}>알림 활성화</div>
                <div style={{ fontSize: 12, color: '#475569', marginTop: 2 }}>이벤트 감지 시 Telegram 메시지 발송</div>
              </div>
              <label style={{ position: 'relative', display: 'inline-block', width: 42, height: 22, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={telegram.enabled}
                  onChange={e => setTelegram({ ...telegram, enabled: e.target.checked })}
                  style={{ opacity: 0, width: 0, height: 0 }}
                />
                <span style={{
                  position: 'absolute', inset: 0,
                  background: telegram.enabled ? '#22d3ee' : '#1e293b',
                  borderRadius: 22,
                  transition: 'background 0.2s',
                  border: '1px solid rgba(255,255,255,0.1)',
                }}>
                  <span style={{
                    position: 'absolute',
                    width: 16, height: 16,
                    background: '#fff',
                    borderRadius: '50%',
                    top: 2,
                    left: telegram.enabled ? 22 : 2,
                    transition: 'left 0.2s',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
                  }} />
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 6 }}>Bot Token</label>
                <input
                  type="password"
                  value={telegram.bot_token}
                  onChange={e => setTelegram({ ...telegram, bot_token: e.target.value })}
                  placeholder="1234567890:ABCDEFxxxxxx"
                />
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 6 }}>Chat ID</label>
                <input
                  type="text"
                  value={telegram.chat_id}
                  onChange={e => setTelegram({ ...telegram, chat_id: e.target.value })}
                  placeholder="-1001234567890"
                />
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#64748b', display: 'block', marginBottom: 10 }}>알림 유형 선택</label>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {EVENT_OPTIONS.map(opt => {
                    const checked = telegram.alert_types.includes(opt.key)
                    return (
                      <label
                        key={opt.key}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 7,
                          padding: '7px 14px', borderRadius: 8,
                          background: checked ? 'rgba(34,211,238,0.08)' : 'rgba(255,255,255,0.03)',
                          border: `1px solid ${checked ? 'rgba(34,211,238,0.2)' : 'rgba(255,255,255,0.06)'}`,
                          cursor: 'pointer',
                          fontSize: 13, fontWeight: 600,
                          color: checked ? '#22d3ee' : '#475569',
                          transition: 'all 0.15s',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={e => {
                            const next = e.target.checked
                              ? [...telegram.alert_types, opt.key]
                              : telegram.alert_types.filter(a => a !== opt.key)
                            setTelegram({ ...telegram, alert_types: next })
                          }}
                          style={{ display: 'none' }}
                        />
                        {checked ? '✓' : '+'} {opt.label}
                      </label>
                    )
                  })}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                <button onClick={saveTelegram} disabled={saving} className="btn-primary">
                  <Save size={13} />
                  {saving ? '저장 중...' : '설정 저장'}
                </button>
                <button onClick={testTelegram} disabled={testing} className="btn-ghost">
                  <Send size={13} />
                  {testing ? '발송 중...' : '테스트 발송'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ─── Zoom ─── */}
        {tab === 'zoom' && (
          <div style={{ maxWidth: 480 }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: '#e2eeff', marginBottom: 4, marginTop: 0 }}>디지털 줌 설정</h2>
            <p style={{ fontSize: 13, color: '#475569', marginBottom: 24, marginTop: 0 }}>
              이상 이벤트 감지 시 특정 영역을 자동으로 확대합니다.
            </p>

            {/* 줌 배율 */}
            <div className="glass" style={{ borderRadius: 14, padding: '20px 22px', marginBottom: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#94a3b8', marginBottom: 16 }}>줌 배율</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <button onClick={() => handleZoomFactor(zoom.zoom_factor - 0.5)} className="btn-ghost" style={{ padding: '8px 12px' }}>
                  <ZoomOut size={16} />
                </button>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <input
                    type="range"
                    min={1} max={8} step={0.5}
                    value={zoom.zoom_factor}
                    onChange={e => handleZoomFactor(parseFloat(e.target.value))}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155' }}>
                    <span>1x</span><span>4x</span><span>8x</span>
                  </div>
                </div>
                <button onClick={() => handleZoomFactor(zoom.zoom_factor + 0.5)} className="btn-ghost" style={{ padding: '8px 12px' }}>
                  <ZoomIn size={16} />
                </button>
              </div>
              <div style={{ textAlign: 'center', fontSize: 28, fontWeight: 800, color: '#22d3ee', fontFamily: 'monospace', marginTop: 12 }}>
                {zoom.zoom_factor.toFixed(1)}×
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={async () => {
                  await apiPost('/zoom/activate', { x: 320, y: 240, factor: zoom.zoom_factor })
                  setZoom(prev => ({ ...prev, active: true }))
                  toast('줌 활성화', { type: 'success' })
                }}
                className="btn-primary"
              >
                줌 활성화
              </button>
              <button
                onClick={async () => {
                  await apiPost('/zoom/deactivate', {})
                  setZoom(prev => ({ ...prev, active: false }))
                  toast('줌 비활성화', { type: 'info' })
                }}
                className="btn-danger"
              >
                비활성화
              </button>
            </div>

            {zoom.active && (
              <div style={{ marginTop: 14, padding: '10px 14px', borderRadius: 9, background: 'rgba(34,211,238,0.06)', border: '1px solid rgba(34,211,238,0.15)', fontSize: 12, color: '#22d3ee' }}>
                ● 줌 {zoom.zoom_factor}× 활성화됨
              </div>
            )}
          </div>
        )}

        {/* ─── Whitelist ─── */}
        {tab === 'whitelist' && (
          <div style={{ maxWidth: 600 }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: '#e2eeff', marginBottom: 4, marginTop: 0 }}>외부인 화이트리스트</h2>
            <p style={{ fontSize: 13, color: '#475569', marginBottom: 24, marginTop: 0 }}>
              등록된 인원은 외부인 감지에서 제외됩니다. 직원, 협력사 인원 등을 등록하세요.
            </p>

            {/* 등록 폼 */}
            <div className="glass" style={{ borderRadius: 14, padding: '16px 18px', marginBottom: 20, display: 'flex', gap: 10, alignItems: 'flex-end' }}>
              <div style={{ flex: 2 }}>
                <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>이름</label>
                <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="홍길동" />
              </div>
              <div style={{ flex: 2 }}>
                <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>역할</label>
                <input type="text" value={newRole} onChange={e => setNewRole(e.target.value)} placeholder="간호사 / 청소업체" />
              </div>
              <button
                onClick={() => toast('얼굴 등록', { type: 'info', message: 'API: POST /faces/register (카메라 프레임 필요)' })}
                className="btn-primary"
                style={{ flexShrink: 0 }}
              >
                <Plus size={13} />
                등록
              </button>
            </div>

            {/* 목록 */}
            {whitelist.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#1e293b', fontSize: 13 }}>
                등록된 인원이 없습니다
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {whitelist.map(w => (
                  <div
                    key={w.id}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px 16px',
                      borderRadius: 11,
                      background: 'rgba(255,255,255,0.02)',
                      border: '1px solid rgba(255,255,255,0.04)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{
                        width: 34, height: 34, borderRadius: '50%',
                        background: 'rgba(34,211,238,0.1)',
                        border: '1px solid rgba(34,211,238,0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 13, fontWeight: 700, color: '#22d3ee',
                      }}>
                        {w.name.charAt(0)}
                      </div>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 600, color: '#e2eeff' }}>{w.name}</div>
                        <div style={{ fontSize: 11, color: '#475569' }}>{w.role || '역할 미지정'}</div>
                      </div>
                    </div>
                    <button onClick={() => removeFace(w.name)} className="btn-danger" style={{ padding: '5px 12px', fontSize: 12 }}>
                      <Trash2 size={12} />
                      삭제
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── GeoFence ─── */}
        {tab === 'geo' && (
          <div style={{ maxWidth: 620 }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: '#e2eeff', marginBottom: 4, marginTop: 0 }}>GeoFence 구역 관리</h2>
            <p style={{ fontSize: 13, color: '#475569', marginBottom: 24, marginTop: 0 }}>
              이탈 감지 구역을 API로 설정합니다. 좌표는 카메라 해상도 기준 픽셀값입니다.
            </p>

            <div className="glass" style={{ borderRadius: 14, padding: '20px', marginBottom: 20 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#64748b', marginBottom: 12 }}>API 엔드포인트</div>
              <pre style={{
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                padding: '14px 16px',
                fontSize: 12,
                color: '#94a3b8',
                overflowX: 'auto',
                lineHeight: 1.7,
                margin: 0,
                border: '1px solid rgba(255,255,255,0.04)',
              }}>
{`POST /geo/set
{
  "zone_id": "ward_a",
  "vertices": [
    [100, 100],
    [540, 100],
    [540, 380],
    [100, 380]
  ]
}

# 응답: 200 OK
{ "status": "ok", "zone_id": "ward_a" }`}
              </pre>
            </div>

            <div style={{ padding: '14px 18px', borderRadius: 12, background: 'rgba(34,211,238,0.04)', border: '1px solid rgba(34,211,238,0.1)', fontSize: 12, color: '#475569', lineHeight: 1.6 }}>
              <span style={{ color: '#22d3ee', fontWeight: 700 }}>팁</span> · Swagger UI (
              <a href="/docs" target="_blank" style={{ color: '#22d3ee', textDecoration: 'none' }}>/docs</a>
              )에서 구역을 대화형으로 설정할 수 있습니다.
              구역은 복수 설정 가능하며, zone_id로 구분합니다.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
