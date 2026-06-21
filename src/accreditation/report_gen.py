import logging
import os
from datetime import datetime
from pathlib import Path

from src.config.settings import REPORT_OUTPUT_DIR

logger = logging.getLogger(__name__)

KOREAN_FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    if os.path.exists(KOREAN_FONT_PATH):
        pdfmetrics.registerFont(TTFont("Malgun", KOREAN_FONT_PATH))
        KOREAN_FONT = "Malgun"
    else:
        KOREAN_FONT = "Helvetica"
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    KOREAN_FONT = None


class AccreditationReport:
    def __init__(self):
        REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def generate(self, events: list[dict], facility_name: str = "medicerti-vision") -> str:
        fall_events = [e for e in events if e.get("event_type") == "fall"]
        elopement_events = [e for e in events if e.get("event_type") == "elopement"]
        loitering_events = [e for e in events if e.get("event_type") == "loitering"]
        stranger_events = [e for e in events if e.get("event_type") == "stranger"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{facility_name}_report_{timestamp}.pdf"
        filepath = REPORT_OUTPUT_DIR / filename

        if HAS_REPORTLAB:
            self._generate_pdf(filepath, events, fall_events, elopement_events,
                               loitering_events, stranger_events, facility_name)
        else:
            filepath = filepath.with_suffix(".html")
            self._generate_html(filepath, events, fall_events, elopement_events,
                                loitering_events, stranger_events, facility_name)

        logger.info(f"Report generated: {filepath}")
        return str(filepath)

    def _generate_pdf(self, filepath: Path, events, fall_events, elopement_events,
                       loitering_events, stranger_events, facility_name):
        doc = SimpleDocTemplate(
            str(filepath), pagesize=A4,
            topMargin=20*mm, bottomMargin=20*mm,
            leftMargin=20*mm, rightMargin=20*mm,
        )
        styles = getSampleStyleSheet()
        s_normal = ParagraphStyle("Normal", fontName=KOREAN_FONT, fontSize=10, leading=14)
        s_title = ParagraphStyle("Title", fontName=KOREAN_FONT, fontSize=18, leading=24, spaceAfter=12)
        s_h1 = ParagraphStyle("H1", fontName=KOREAN_FONT, fontSize=14, leading=20, spaceBefore=16, spaceAfter=8)
        s_h2 = ParagraphStyle("H2", fontName=KOREAN_FONT, fontSize=12, leading=16, spaceBefore=12, spaceAfter=6)
        s_small = ParagraphStyle("Small", fontName=KOREAN_FONT, fontSize=8, leading=10, textColor=colors.gray)

        elements = []

        elements.append(Paragraph("의료기관 인증평가 대응 - 환자 안전 보고서", s_title))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2b6cb0")))
        elements.append(Spacer(1, 6*mm))

        period_text = "N/A"
        if events:
            period_text = f"{events[-1]['timestamp'][:10]} ~ {events[0]['timestamp'][:10]}"
        elements.append(Paragraph(
            f"<b>기관:</b> {facility_name} &nbsp;&nbsp; <b>생성일:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;&nbsp; <b>분석 기간:</b> {period_text}",
            s_normal,
        ))
        elements.append(Spacer(1, 8*mm))

        elements.append(Paragraph("통계 요약", s_h1))

        stats = [
            ["항목", "건수"],
            ["낙상 감지", str(len(fall_events))],
            ["이탈 감지", str(len(elopement_events))],
            ["배회 감지", str(len(loitering_events))],
            ["미등록 외부인", str(len(stranger_events))],
            ["전체", str(len(events))],
        ]
        t = Table(stats, colWidths=[120*mm, 40*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), KOREAN_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 8*mm))

        if events:
            elements.append(Paragraph("전체 이벤트 목록", s_h1))
            event_data = [["시간", "카메라", "유형", "신뢰도", "세부 정보"]]
            for e in events[:100]:
                details = e.get("details", {})
                details_str = "; ".join(f"{k}: {v}" for k, v in details.items()) if details else "-"
                event_data.append([
                    e.get("timestamp", "")[:19],
                    e.get("camera_id", ""),
                    self._event_type_kor(e.get("event_type", "")),
                    f"{e.get('confidence', 0):.0%}",
                    details_str,
                ])
            et = Table(event_data, colWidths=[45*mm, 30*mm, 25*mm, 20*mm, 50*mm])
            et.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), KOREAN_FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (2, 0), (3, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(et)

        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("medicerti-vision | Medical Edge Vision AI SaaS | 자동 생성 보고서", s_small))

        doc.build(elements)

    def _generate_html(self, filepath: Path, events, fall_events, elopement_events,
                        loitering_events, stranger_events, facility_name):
        period_text = "N/A"
        if events:
            period_text = f"{events[-1]['timestamp'][:10]} ~ {events[0]['timestamp'][:10]}"

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
<h1>의료기관 인증평가 대응 - 환자 안전 보고서</h1>
<p><strong>기관:</strong> {facility_name} | <strong>생성일:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<p><strong>분석 기간:</strong> {period_text}</p>

<div class="stat-card"><div class="stat-number">{len(fall_events)}</div>낙상 감지</div>
<div class="stat-card"><div class="stat-number">{len(elopement_events)}</div>이탈 감지</div>
<div class="stat-card"><div class="stat-number">{len(loitering_events)}</div>배회 감지</div>
<div class="stat-card"><div class="stat-number">{len(stranger_events)}</div>미등록 외부인</div>

<h2>전체 이벤트 목록</h2>
<table>
<tr><th>시간</th><th>카메라</th><th>유형</th><th>신뢰도</th><th>세부 정보</th></tr>
{"".join(self._event_row(e) for e in events[:100])}
</table>
<div class="footer">medicerti-vision | Medical Edge Vision AI SaaS | 자동 생성 보고서</div>
</body></html>"""

        filepath.write_text(html, encoding="utf-8")

    def _event_row(self, event: dict) -> str:
        details = event.get("details", {})
        details_str = "; ".join(f"{k}: {v}" for k, v in details.items()) if details else "-"
        return (f"<tr><td>{event.get('timestamp', '')[:19]}</td>"
                f"<td>{event.get('camera_id', '')}</td>"
                f"<td>{self._event_type_kor(event.get('event_type', ''))}</td>"
                f"<td>{event.get('confidence', 0):.0%}</td>"
                f"<td>{details_str}</td></tr>")

    @staticmethod
    def _event_type_kor(event_type: str) -> str:
        return {
            "fall": "낙상",
            "elopement": "이탈",
            "loitering": "배회",
            "stranger": "미등록 외부인",
        }.get(event_type, event_type)
