import { useState } from "react"
import { ZoomIn, ZoomOut, FileText, Eye } from "lucide-react"
import type { DetectionEvent, ZoomInfo } from "../types"
import { apiPost, apiGet } from "../lib/utils"
import type { ReportResult } from "../types"

interface Props {
  selectedEvent: DetectionEvent | null
  zoomInfo: ZoomInfo
  onZoomChange: (z: ZoomInfo) => void
  typeLabels: Record<string, string>
}

export default function MainPanel({ selectedEvent, zoomInfo, onZoomChange, typeLabels }: Props) {
  const [reportLoading, setReportLoading] = useState<string | null>(null)
  const [zoomFactor, setZoomFactor] = useState(2.0)

  const generateReport = async (type: string) => {
    setReportLoading(type)
    try {
      const result = await apiPost<ReportResult>(`/events/report-${type}`, {})
      window.open(`${window.location.origin}/${result.pdf_path.replace(/\\/g, "/").replace("D:/medicerti-vision/", "")}`, "_blank")
    } catch (e) {
      alert(`보고서 생성 실패: ${String(e)}`)
    } finally {
      setReportLoading(null)
    }
  }

  const handleZoom = async (action: string) => {
    try {
      if (action === "in") {
        const f = Math.min(8, zoomFactor + 0.5)
        await apiPost("/zoom/factor", { factor: f })
        setZoomFactor(f)
        onZoomChange({ ...zoomInfo, zoom_factor: f })
      } else if (action === "out") {
        const f = Math.max(1, zoomFactor - 0.5)
        await apiPost("/zoom/factor", { factor: f })
        setZoomFactor(f)
        onZoomChange({ ...zoomInfo, zoom_factor: f })
      }
    } catch { /* ignore */ }
  }

  return (
    <div className="flex-1 flex gap-4">
      <div className="flex-1 space-y-4">
        <div className="bg-[#1e293b] rounded-lg border border-[#334155] p-6 flex flex-col items-center justify-center min-h-[300px] text-[#64748b]">
          <Eye className="w-12 h-12 mb-3 opacity-50" />
          <p className="text-sm">라이브 영상 영역</p>
          <p className="text-xs mt-1">RTSP 카메라 연결 시 실시간 스트림이 표시됩니다</p>
          {zoomInfo.active && (
            <div className="mt-3 flex items-center gap-2 text-xs text-[#38bdf8]">
              <ZoomIn className="w-3 h-3" />
              줌 {zoomInfo.zoom_factor}x 활성화
            </div>
          )}
          {selectedEvent && typeof selectedEvent.details?.snapshot_b64 === "string" && (
            <img
              src={`data:image/jpeg;base64,${selectedEvent.details.snapshot_b64}`}
              alt="snapshot"
              className="mt-3 max-h-48 rounded border border-[#334155]"
            />
          )}
        </div>

        <div className="bg-[#1e293b] rounded-lg border border-[#334155] p-4">
          <h3 className="text-sm font-semibold text-[#94a3b8] mb-3">디지털 줌 컨트롤</h3>
          <div className="flex items-center gap-3">
            <button onClick={() => handleZoom("out")} className="p-2 bg-[#334155] rounded hover:bg-[#475569] transition-colors">
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm font-mono w-12 text-center">{zoomFactor.toFixed(1)}x</span>
            <button onClick={() => handleZoom("in")} className="p-2 bg-[#334155] rounded hover:bg-[#475569] transition-colors">
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="w-64 space-y-3">
        <div className="bg-[#1e293b] rounded-lg border border-[#334155] p-4">
          <h3 className="text-sm font-semibold text-[#94a3b8] mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" /> 보고서 생성
          </h3>
          <div className="space-y-2">
            {[
              { key: "pdf", label: "통합 보고서" },
              { key: "night", label: "야간 관찰 일지" },
              { key: "highrisk", label: "위험군 관찰 기록" },
              { key: "access", label: "출입 통제 로그" },
            ].map((r) => (
              <button
                key={r.key}
                onClick={() => generateReport(r.key)}
                disabled={reportLoading === r.key}
                className="w-full text-left px-3 py-2 text-sm bg-[#0f172a] rounded hover:bg-[#334155] transition-colors disabled:opacity-50"
              >
                {reportLoading === r.key ? "생성 중..." : r.label}
              </button>
            ))}
          </div>
        </div>

        {selectedEvent && (
          <div className="bg-[#1e293b] rounded-lg border border-[#334155] p-4">
            <h3 className="text-sm font-semibold text-[#94a3b8] mb-2">선택된 이벤트</h3>
            <div className="text-xs space-y-1 text-[#94a3b8]">
              <div><span className="text-[#64748b]">유형:</span> {typeLabels[selectedEvent.event_type]}</div>
              <div><span className="text-[#64748b]">신뢰도:</span> {(selectedEvent.confidence * 100).toFixed(0)}%</div>
              <div><span className="text-[#64748b]">카메라:</span> {selectedEvent.camera_id}</div>
              <div><span className="text-[#64748b]">시간:</span> {selectedEvent.timestamp}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
