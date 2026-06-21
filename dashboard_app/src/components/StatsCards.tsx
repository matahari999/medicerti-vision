import type { EventStats } from "../types"

interface Props {
  stats: EventStats
  typeLabels: Record<string, string>
}

const colors: Record<string, { text: string; bg: string; border: string }> = {
  fall: { text: "text-red-400", bg: "bg-red-500/10", border: "border-red-500" },
  elopement: { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500" },
  loitering: { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500" },
  stranger: { text: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500" },
}

const keys = ["fall", "elopement", "loitering", "stranger"] as const

export default function StatsCards({ stats, typeLabels }: Props) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {keys.map((k) => (
        <div key={k} className={`rounded-lg p-4 text-center border-l-4 ${colors[k].bg} ${colors[k].border} ${colors[k].text}`}>
          <div className="text-3xl font-bold">{stats[k]}</div>
          <div className="text-xs mt-1 text-[#94a3b8]">{typeLabels[k]}</div>
        </div>
      ))}
    </div>
  )
}
