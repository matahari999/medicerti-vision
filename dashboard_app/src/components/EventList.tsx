import { useEffect, useRef } from "react"
import type { DetectionEvent } from "../types"

interface Props {
  events: DetectionEvent[]
  typeLabels: Record<string, string>
  onSelect: (e: DetectionEvent) => void
}

const borderColors: Record<string, string> = {
  fall: "border-l-red-500",
  elopement: "border-l-amber-500",
  loitering: "border-l-orange-500",
  stranger: "border-l-purple-500",
}

const badgeColors: Record<string, string> = {
  fall: "bg-red-500",
  elopement: "bg-amber-500 text-black",
  loitering: "bg-orange-500",
  stranger: "bg-purple-500",
}

export default function EventList({ events, typeLabels, onSelect }: Props) {
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (listRef.current && events.length > 0) {
      listRef.current.scrollTop = 0
    }
  }, [events.length])

  return (
    <div className="w-80 border-r border-[#334155] bg-[#1e293b] flex flex-col">
      <div className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[#64748b] border-b border-[#334155]">
        최근 이벤트 ({events.length})
      </div>
      <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-1">
        {events.length === 0 && (
          <div className="text-center py-10 text-[#64748b] text-sm">이벤트가 아직 없습니다</div>
        )}
        {events.map((e) => (
          <div
            key={e.id}
            onClick={() => onSelect(e)}
            className={`border-l-4 ${borderColors[e.event_type] || "border-l-gray-500"} bg-[#0f172a] rounded-md p-3 cursor-pointer hover:bg-[#334155] transition-colors`}
          >
            <div className="flex items-center justify-between text-xs text-[#94a3b8]">
              <span>{formatTime(e.timestamp)}</span>
              <span>{e.camera_id}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm font-medium">{typeLabels[e.event_type] || e.event_type}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${badgeColors[e.event_type] || "bg-gray-500"} text-white`}>
                {(e.confidence * 100).toFixed(0)}%
              </span>
            </div>
            {e.details && Object.keys(e.details).length > 0 && (
              <div className="text-xs text-[#64748b] mt-1 truncate">
                {Object.entries(e.details).slice(0, 2).map(([k, v]) => `${k}: ${String(v)}`).join(" | ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
  } catch {
    return ts
  }
}
