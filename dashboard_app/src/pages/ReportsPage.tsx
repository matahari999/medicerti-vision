import { useState } from "react"
import { FileText, Moon, AlertTriangle, DoorOpen, Download, CheckCircle, Loader } from "lucide-react"
import { apiPost } from "../lib/utils"
import type { ReportResult } from "../types"
import { useToast } from "../hooks/useToast"

const REPORTS = [
  {
    key: 'pdf',
    icon: FileText,
    color: '#22d3ee',
    bg: 'rgba(34,211,238,0.08)',
    border: 'rgba(34,211,238,0.15)',
    title: '통합 보고서',
    desc: '전체 감지 이벤트 종합 분석 리포트',
    badge: '일반',
  },
  {
    key: 'night',
    icon: Moon,
    color: '#c084fc',
    bg: 'rgba(192,132,252,0.08)',
    border: 'rgba(192,132,252,0.15)',
    title: '야간 보안 관찰 일지',
    desc: '야간 (22:00–06:00) 이상 행동 관찰 서식',
    badge: '인증평가',
  },
  {
    key: 'highrisk',
    icon: AlertTriangle,
    color: '#f87171',
    bg: 'rgba(248,113,113,0.08)',
    border: 'rgba(248,113,113,0.15)',
    title: '위험 고위험군 관찰 기록',
    desc: '낙상·이탈 위험 환자 집중 관찰 기록지',
    badge: '인증평가',
  },
  {
    key: 'access',
    icon: DoorOpen,
    color: '#fb923c',
    bg: 'rgba(251,146,60,0.08)',
    border: 'rgba(251,146,60,0.15)',
    title: '외부인 출입 통제 로그',
    desc: '미등록 외부인 감지 및 출입 통제 현황',
    badge: '인증평가',
  },
]

export default function ReportsPage() {
  const [loading, setLoading] = useState<string | null>(null)
  const [generated, setGenerated] = useState<Record<string, string>>({})
  const { toast } = useToast()

  const generate = async (key: string) => {
    setLoading(key)
    try {
      const result = await apiPost<ReportResult>(`/events/report-${key}`, {})
      const url = `${window.location.origin}/${result.pdf_path.replace(/\\/g, '/').replace(/^.*?medicerti-vision[\\/]/, '')}`
      setGenerated(prev => ({ ...prev, [key]: url }))
      toast('보고서 생성 완료', { type: 'success', message: `PDF 파일이 생성되었습니다.` })
    } catch (e) {
      toast('보고서 생성 실패', { type: 'error', message: String(e) })
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="page-enter" style={{ padding: 24, maxWidth: 900 }}>

      {/* 헤더 설명 */}
      <div
        className="glass"
        style={{ borderRadius: 14, padding: '16px 20px', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 14 }}
      >
        <div style={{
          width: 40, height: 40, borderRadius: 11,
          background: 'rgba(34,211,238,0.1)',
          border: '1px solid rgba(34,211,238,0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <FileText size={18} color="#22d3ee" />
        </div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e2eeff', marginBottom: 2 }}>인증평가 서식 자동 생성</div>
          <div style={{ fontSize: 12, color: '#475569' }}>
            AI가 감지한 이벤트 데이터를 기반으로 의료기관 인증평가 서식에 맞는 PDF 보고서를 자동 생성합니다.
          </div>
        </div>
      </div>

      {/* 보고서 카드 그리드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
        {REPORTS.map((r, i) => {
          const { icon: Icon } = r
          const isLoading = loading === r.key
          const isDone = !!generated[r.key]

          return (
            <div
              key={r.key}
              className="glass glass-hover card-enter"
              style={{
                borderRadius: 16,
                padding: '22px 22px',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                animationDelay: `${i * 0.07}s`,
              }}
            >
              {/* 아이콘 + 배지 */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div style={{
                  width: 46, height: 46, borderRadius: 12,
                  background: r.bg,
                  border: `1px solid ${r.border}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: `0 0 20px ${r.bg}`,
                }}>
                  <Icon size={20} color={r.color} />
                </div>
                <span style={{
                  fontSize: 10, fontWeight: 700,
                  padding: '3px 9px', borderRadius: 100,
                  background: r.bg, color: r.color, border: `1px solid ${r.border}`,
                  letterSpacing: '0.04em',
                }}>
                  {r.badge}
                </span>
              </div>

              {/* 설명 */}
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#e2eeff', marginBottom: 5 }}>{r.title}</div>
                <div style={{ fontSize: 12, color: '#475569', lineHeight: 1.5 }}>{r.desc}</div>
              </div>

              {/* 버튼 영역 */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => generate(r.key)}
                  disabled={isLoading}
                  className="btn-primary"
                  style={{ flex: 1, justifyContent: 'center', background: isLoading ? undefined : r.color !== '#22d3ee' ? r.bg : undefined }}
                >
                  {isLoading ? (
                    <>
                      <Loader size={13} style={{ animation: 'spin 1s linear infinite' }} />
                      생성 중...
                    </>
                  ) : isDone ? (
                    <>
                      <CheckCircle size={13} />
                      재생성
                    </>
                  ) : (
                    <>
                      <FileText size={13} />
                      PDF 생성
                    </>
                  )}
                </button>

                {isDone && (
                  <a
                    href={generated[r.key]}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-ghost"
                  >
                    <Download size={13} />
                    열기
                  </a>
                )}
              </div>

              {isDone && (
                <div style={{
                  fontSize: 11, color: '#22c55e',
                  display: 'flex', alignItems: 'center', gap: 5,
                  padding: '6px 10px',
                  borderRadius: 7,
                  background: 'rgba(34,197,94,0.06)',
                  border: '1px solid rgba(34,197,94,0.15)',
                }}>
                  <CheckCircle size={11} />
                  PDF가 생성되었습니다
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* 안내 */}
      <div style={{ marginTop: 24, padding: '14px 18px', borderRadius: 12, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', fontSize: 12, color: '#334155', lineHeight: 1.6 }}>
        <span style={{ color: '#475569', fontWeight: 600 }}>안내</span> · 생성된 PDF는{' '}
        <code style={{ fontSize: 11, color: '#22d3ee', background: 'rgba(34,211,238,0.08)', padding: '1px 6px', borderRadius: 4 }}>data/reports/</code>{' '}
        폴더에 저장됩니다. 이벤트 데이터가 없는 경우 빈 서식이 생성될 수 있습니다.
      </div>
    </div>
  )
}
