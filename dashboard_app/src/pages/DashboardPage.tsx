import { useState } from "react"
import { useAppState } from "../context/AppContext"
import StatCard from "../components/StatCard"
import EventFeed from "../components/EventFeed"
import CameraPanel from "../components/CameraPanel"
import ActivityChart from "../components/ActivityChart"
import type { DetectionEvent } from "../types"

export default function DashboardPage() {
  const { events, stats, connected } = useAppState()
  const [selected, setSelected] = useState<DetectionEvent | null>(null)

  return (
    <div className="page-enter" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20, minHeight: 0 }}>

      {/* 상단 연결 배너 (미연결 시) */}
      {!connected && (
        <div style={{
          padding: '10px 16px',
          borderRadius: 10,
          background: 'rgba(251,191,36,0.06)',
          border: '1px solid rgba(251,191,36,0.18)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: 13,
          color: '#fbbf24',
        }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#fbbf24', flexShrink: 0 }} />
          <span><strong>WebSocket 연결 대기 중</strong> — AI 엔진 서버에 연결되면 실시간 이벤트가 표시됩니다.</span>
        </div>
      )}

      {/* 통계 카드 4개 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        <StatCard type="fall"      value={stats.fall} />
        <StatCard type="elopement" value={stats.elopement} />
        <StatCard type="loitering" value={stats.loitering} />
        <StatCard type="stranger"  value={stats.stranger} />
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 16, minHeight: 0 }}>

        {/* 왼쪽: 카메라 + 선택 이벤트 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* 카메라 패널 */}
          <div
            className="glass"
            style={{ borderRadius: 16, padding: '18px 20px' }}
          >
            <CameraPanel connected={connected} events={events} />
          </div>

          {/* 선택된 이벤트 스냅샷 */}
          {selected && (
            <div
              className="glass card-enter"
              style={{ borderRadius: 16, padding: '18px 20px' }}
            >
              <div style={{ fontSize: 12, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>
                선택된 이벤트 상세
              </div>
              <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
                {/* 스냅샷 */}
                {typeof selected.details?.snapshot_b64 === 'string' ? (
                  <img
                    src={`data:image/jpeg;base64,${selected.details.snapshot_b64}`}
                    alt="snapshot"
                    style={{ width: 180, height: 110, objectFit: 'cover', borderRadius: 10, border: '1px solid rgba(255,255,255,0.08)' }}
                  />
                ) : (
                  <div style={{
                    width: 180, height: 110,
                    borderRadius: 10,
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid rgba(255,255,255,0.04)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11, color: '#334155',
                  }}>
                    스냅샷 없음
                  </div>
                )}
                {/* 메타데이터 */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {[
                    { label: '이벤트 유형', value: selected.event_type },
                    { label: '카메라 ID',   value: selected.camera_id },
                    { label: '신뢰도',      value: `${(selected.confidence * 100).toFixed(1)}%` },
                    { label: '감지 시각',   value: new Date(selected.timestamp).toLocaleString('ko-KR') },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <div style={{ fontSize: 10, color: '#334155', marginBottom: 1 }}>{label}</div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8' }}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 활동 차트 */}
          <div className="glass" style={{ borderRadius: 16, padding: '18px 20px' }}>
            <ActivityChart events={events} />
          </div>
        </div>

        {/* 오른쪽: 이벤트 피드 */}
        <div
          className="glass"
          style={{
            borderRadius: 16,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            maxHeight: 'calc(100vh - 200px)',
          }}
        >
          <EventFeed
            events={events}
            onSelect={setSelected}
            selected={selected}
            maxHeight={99999}
          />
        </div>
      </div>
    </div>
  )
}
