import { Settings, Activity } from "lucide-react"

interface Props {
  connected: boolean
  onToggleSettings: () => void
  showSettings: boolean
}

export default function Header({ connected, onToggleSettings, showSettings }: Props) {
  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-[#334155] bg-gradient-to-r from-[#1e293b] to-[#334155]">
      <div className="flex items-center gap-3">
        <Activity className="w-5 h-5 text-[#38bdf8]" />
        <h1 className="text-lg font-semibold text-[#38bdf8]">medicerti-vision</h1>
        <span className="text-xs text-[#64748b]">실시간 환자 안전 모니터링</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-500 shadow-[0_0_6px_#22c55e]" : "bg-red-500"}`} />
          <span className="text-[#94a3b8]">{connected ? "연결됨" : "연결 끊김"}</span>
        </div>
        <button
          onClick={onToggleSettings}
          className={`p-2 rounded-lg transition-colors ${showSettings ? "bg-[#38bdf8] text-[#0f172a]" : "text-[#94a3b8] hover:bg-[#334155]"}`}
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
