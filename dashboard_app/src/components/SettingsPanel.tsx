import { useState, useEffect } from "react"
import { ArrowLeft, Save, Bell, Camera, Users, MapPin } from "lucide-react"
import type { ZoomInfo, TelegramConfig, WhitelistEntry } from "../types"
import { apiPost, apiGet } from "../lib/utils"

interface Props {
  onClose: () => void
  zoomInfo: ZoomInfo
  onZoomChange: (z: ZoomInfo) => void
}

export default function SettingsPanel({ onClose, zoomInfo, onZoomChange }: Props) {
  const [tab, setTab] = useState("telegram")
  const [telegram, setTelegram] = useState<TelegramConfig>({
    enabled: false, bot_token: "", chat_id: "", alert_types: ["fall"],
  })
  const [whitelist, setWhitelist] = useState<WhitelistEntry[]>([])
  const [saving, setSaving] = useState<string | null>(null)

  useEffect(() => {
    apiGet<TelegramConfig>("/notify/config").then(setTelegram).catch(() => {})
    apiGet<WhitelistEntry[]>("/faces/whitelist").then(setWhitelist).catch(() => {})
  }, [])

  const saveTelegram = async () => {
    setSaving("telegram")
    try {
      await apiPost("/notify/config", telegram)
    } catch { /* ignore */ }
    setSaving(null)
  }

  const removeFace = async (name: string) => {
    try {
      await apiPost("/faces/remove", { name })
      setWhitelist((prev) => prev.filter((w) => w.name !== name))
    } catch { /* ignore */ }
  }

  const tabs = [
    { key: "telegram", label: "Telegram", icon: Bell },
    { key: "zoom", label: "줌 설정", icon: Camera },
    { key: "whitelist", label: "외부인 관리", icon: Users },
    { key: "geo", label: "GeoFence", icon: MapPin },
  ]

  return (
    <div className="flex-1 flex flex-col p-4 overflow-y-auto">
      <div className="flex items-center gap-3 mb-4">
        <button onClick={onClose} className="p-2 bg-[#334155] rounded-lg hover:bg-[#475569] transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <h2 className="text-lg font-semibold">설정</h2>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${tab === t.key ? "bg-[#38bdf8] text-[#0f172a]" : "bg-[#1e293b] text-[#94a3b8] hover:bg-[#334155]"}`}
          >
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 bg-[#1e293b] rounded-lg border border-[#334155] p-6">
        {tab === "telegram" && (
          <div className="space-y-4 max-w-lg">
            <h3 className="font-semibold">Telegram 알림 설정</h3>
            <label className="flex items-center gap-3 text-sm">
              <input
                type="checkbox"
                checked={telegram.enabled}
                onChange={(e) => setTelegram({ ...telegram, enabled: e.target.checked })}
                className="w-4 h-4"
              />
              알림 활성화
            </label>
            <div>
              <label className="text-xs text-[#94a3b8]">Bot Token</label>
              <input
                type="password"
                value={telegram.bot_token}
                onChange={(e) => setTelegram({ ...telegram, bot_token: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-[#0f172a] border border-[#334155] rounded text-sm focus:outline-none focus:border-[#38bdf8]"
              />
            </div>
            <div>
              <label className="text-xs text-[#94a3b8]">Chat ID</label>
              <input
                value={telegram.chat_id}
                onChange={(e) => setTelegram({ ...telegram, chat_id: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-[#0f172a] border border-[#334155] rounded text-sm focus:outline-none focus:border-[#38bdf8]"
              />
            </div>
            <div>
              <label className="text-xs text-[#94a3b8]">알림 유형</label>
              <div className="flex gap-3 mt-1">
                {["fall", "elopement", "loitering", "stranger"].map((t) => (
                  <label key={t} className="flex items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={telegram.alert_types.includes(t)}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...telegram.alert_types, t]
                          : telegram.alert_types.filter((a) => a !== t)
                        setTelegram({ ...telegram, alert_types: next })
                      }}
                    />
                    {t}
                  </label>
                ))}
              </div>
            </div>
            <button
              onClick={saveTelegram}
              disabled={saving === "telegram"}
              className="flex items-center gap-2 px-4 py-2 bg-[#38bdf8] text-[#0f172a] rounded-lg text-sm font-medium hover:bg-[#7dd3fc] transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" /> {saving === "telegram" ? "저장 중..." : "저장"}
            </button>
          </div>
        )}

        {tab === "zoom" && (
          <div className="space-y-4 max-w-lg">
            <h3 className="font-semibold">디지털 줌 설정</h3>
            <div>
              <label className="text-xs text-[#94a3b8]">줌 배율 (1.0 ~ 8.0)</label>
              <input
                type="range"
                min="1"
                max="8"
                step="0.5"
                value={zoomInfo.zoom_factor}
                onChange={(e) => onZoomChange({ ...zoomInfo, zoom_factor: parseFloat(e.target.value) })}
                className="w-full mt-2"
              />
              <div className="text-center text-sm mt-1">{zoomInfo.zoom_factor}x</div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  await apiPost("/zoom/activate", { x: 320, y: 240, factor: zoomInfo.zoom_factor })
                  onZoomChange({ ...zoomInfo, active: true })
                }}
                className="px-4 py-2 bg-[#38bdf8] text-[#0f172a] rounded-lg text-sm font-medium"
              >
                줌 활성화
              </button>
              <button
                onClick={async () => {
                  await apiPost("/zoom/deactivate", {})
                  onZoomChange({ ...zoomInfo, active: false })
                }}
                className="px-4 py-2 bg-[#ef4444] text-white rounded-lg text-sm font-medium"
              >
                비활성화
              </button>
            </div>
          </div>
        )}

        {tab === "whitelist" && (
          <div className="space-y-4 max-w-lg">
            <h3 className="font-semibold">외부인 화이트리스트</h3>
            {whitelist.length === 0 ? (
              <p className="text-sm text-[#64748b]">등록된 얼굴이 없습니다</p>
            ) : (
              <div className="space-y-2">
                {whitelist.map((w) => (
                  <div key={w.id} className="flex items-center justify-between p-3 bg-[#0f172a] rounded-lg">
                    <div>
                      <div className="text-sm font-medium">{w.name}</div>
                      <div className="text-xs text-[#64748b]">{w.role || "—"}</div>
                    </div>
                    <button onClick={() => removeFace(w.name)} className="text-xs text-red-400 hover:text-red-300">
                      삭제
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === "geo" && (
          <div className="space-y-4 max-w-lg">
            <h3 className="font-semibold">GeoFence 구역 관리</h3>
            <p className="text-sm text-[#64748b]">
              GeoFence 구역은 API를 통해 설정합니다. <code className="text-[#38bdf8]">POST /geo/set</code> 엔드포인트를 사용하세요.
            </p>
            <div className="p-4 bg-[#0f172a] rounded-lg">
              <pre className="text-xs text-[#94a3b8]">{JSON.stringify({
                zone_id: "ward_a",
                vertices: [[100, 100], [400, 100], [400, 300], [100, 300]]
              }, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
