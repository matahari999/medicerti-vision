import logging
from datetime import datetime
from pathlib import Path

from src.config.settings import REPORT_OUTPUT_DIR

logger = logging.getLogger(__name__)


class AccreditationReport:
    def __init__(self):
        REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def generate(self, events: list[dict], facility_name: str = "medicerti-vision") -> str:
        fall_events = [e for e in events if e.get("event_type") == "fall"]
        elopement_events = [e for e in events if e.get("event_type") == "elopement"]
        loitering_events = [e for e in events if e.get("event_type") == "loitering"]
        stranger_events = [e for e in events if e.get("event_type") == "stranger"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{facility_name}_report_{timestamp}.html"
        filepath = REPORT_OUTPUT_DIR / filename

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>환자 안전 보고서 - {facility_name}</title>
<style>
body {{ font-family: 'Malgun Gothic', sans-serif; margin: 40px; }}
h1 {{ color: #1a365d; border-bottom: 3px solid #2b6cb0; padding-bottom: 8px; }}
h2 {{ color: #2d3748; margin-top: 30px; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th {{ background: #2b6cb0; color: white; padding: 10px; }}
td, th {{ border: 1px solid #e2e8f0; padding: 8px; text-align: left; }}
tr:nth-child(even) {{ background: #f7fafc; }}
.stat-card {{ display: inline-block; margin: 8px; padding: 16px 24px;
  background: #ebf8ff; border-radius: 8px; border-left: 4px solid #2b6cb0; }}
.stat-number {{ font-size: 28px; font-weight: bold; color: #2b6cb0; }}
.footer {{ margin-top: 40px; color: #718096; font-size: 12px; text-align: center; }}
</style></head><body>
<h1>🔬 의료기관 인증평가 대응 - 환자 안전 보고서</h1>
<p><strong>기관:</strong> {facility_name} | <strong>생성일:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<p><strong>분석 기간:</strong> {events[0]['timestamp'][:10] if events else 'N/A'} ~ {events[-1]['timestamp'][:10] if events else 'N/A'}</p>

<div class="stat-card"><div class="stat-number">{len(fall_events)}</div>낙상 감지</div>
<div class="stat-card"><div class="stat-number">{len(elopement_events)}</div>이탈 감지</div>
<div class="stat-card"><div class="stat-number">{len(loitering_events)}</div>배회 감지</div>
<div class="stat-card"><div class="stat-number">{len(stranger_events)}</div>미등록 외부인</div>

<h2>📋 전체 이벤트 목록</h2>
<table>
<tr><th>시간</th><th>카메라</th><th>유형</th><th>신뢰도</th><th>세부 정보</th></tr>
{"".join(self._event_row(e) for e in events[:100])}
</table>
<div class="footer">medicerti-vision | Medical Edge Vision AI SaaS | 자동 생성 보고서</div>
</body></html>"""

        filepath.write_text(html, encoding="utf-8")
        logger.info(f"Report generated: {filepath}")
        return str(filepath)

    def _event_row(self, event: dict) -> str:
        details = event.get("details", {})
        details_str = "; ".join(f"{k}: {v}" for k, v in details.items()) if details else "-"
        return f"<tr><td>{event.get('timestamp', '')[:19]}</td>" \
               f"<td>{event.get('camera_id', '')}</td>" \
               f"<td>{event.get('event_type', '')}</td>" \
               f"<td>{event.get('confidence', 0):.2%}</td>" \
               f"<td>{details_str}</td></tr>"
