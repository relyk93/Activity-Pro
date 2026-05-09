"""
PDF Export Utility for ActivityPro
- Wall calendar: HTML (landscape, browser print)
- Resident care report: True PDF via reportlab (no browser needed)
"""
import io
from datetime import date, timedelta

def build_weekly_calendar_html(events, week_start, facility_name="ActivityPro Facility"):
    """Build a print-ready HTML weekly calendar."""
    week_end = week_start + timedelta(days=6)
    days = [week_start + timedelta(days=i) for i in range(7)]

    events_by_date = {}
    for ev in events:
        d = ev['date']
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(ev)

    cat_colors = {
        "physical": ("#DEF0DE", "#2A5A2A"),
        "mindful": ("#EBE4F5", "#4A2A7A"),
        "social": ("#DDE8F5", "#1A3A6A"),
        "cognitive": ("#F5EDDD", "#6A4A1A"),
        "creative": ("#FBF0EA", "#6A2A0A"),
        "special_needs": ("#F0EDF8", "#3A2A5A"),
    }

    day_cols = ""
    for day in days:
        day_str = str(day)
        is_today = day == date.today()
        day_events = events_by_date.get(day_str, [])
        header_bg = "#4A6B4C" if is_today else "#2C3E50"
        header_color = "white"

        events_html = ""
        for ev in day_events:
            cat = ev.get('category', 'social')
            bg, fg = cat_colors.get(cat, ("#F5F5F5", "#333"))
            is_special = ev.get('group_type') == 'special_needs'
            border = f"border-left: 3px solid #9B8EC4;" if is_special else ""
            events_html += f"""
            <div style='background:{bg}; color:{fg}; border-radius:6px; padding:6px 8px;
                        margin-bottom:6px; font-size:11px; {border}'>
                <div style='font-weight:700;'>{ev.get('time','')}</div>
                <div style='font-weight:600; margin-top:2px;'>{'🟣 ' if is_special else ''}{ev['title']}</div>
                <div style='font-size:10px; margin-top:2px; opacity:0.8;'>📍 {ev.get('location','Activity Room')}</div>
                <div style='font-size:10px; opacity:0.8;'>💰 {ev.get('cost_estimate','Free')}</div>
            </div>"""

        if not events_html:
            events_html = "<div style='color:#A0AEC0; font-size:11px; text-align:center; padding:12px 0;'>No activities scheduled</div>"

        day_cols += f"""
        <td style='vertical-align:top; border:1px solid #E2DDD6; padding:0; width:14.28%;'>
            <div style='background:{header_bg}; color:{header_color}; padding:8px; text-align:center;'>
                <div style='font-size:11px; text-transform:uppercase; letter-spacing:1px; opacity:0.85;'>{day.strftime("%a")}</div>
                <div style='font-size:20px; font-weight:700; margin-top:2px;'>{day.day}</div>
                {'<div style="font-size:9px; background:rgba(255,255,255,0.3); border-radius:4px; padding:1px 6px; display:inline-block; margin-top:2px;">TODAY</div>' if is_today else ''}
            </div>
            <div style='padding:8px;'>{events_html}</div>
        </td>"""

    legend_html = ""
    for cat, (bg, fg) in cat_colors.items():
        label = "Special Needs" if cat == "special_needs" else cat.title()
        legend_html += f"<span style='display:inline-block; background:{bg}; color:{fg}; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; margin:2px;'>{label}</span>"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Activity Calendar — {facility_name}</title>
<style>
  @page {{ size: landscape; margin: 0.5in; }}
  @media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: Georgia, serif; background: white; margin: 0; padding: 0; }}
  h1 {{ font-family: Georgia, serif; }}
</style>
</head>
<body>
  <!-- Header -->
  <div style='text-align:center; padding:16px 0 12px; border-bottom:2px solid #4A6B4C; margin-bottom:16px;'>
    <div style='font-size:24px; margin-bottom:4px;'>🌸</div>
    <h1 style='margin:0; font-size:22px; color:#1A2332; font-weight:400; letter-spacing:1px;'>{facility_name}</h1>
    <p style='margin:4px 0 0; color:#718096; font-size:13px;'>
      Weekly Activity Calendar &nbsp;·&nbsp;
      {week_start.strftime("%B %d")} – {week_end.strftime("%B %d, %Y")}
    </p>
  </div>

  <!-- Calendar Grid -->
  <table style='width:100%; border-collapse:collapse; table-layout:fixed;'>
    <tr>{day_cols}</tr>
  </table>

  <!-- Legend -->
  <div style='margin-top:16px; padding:12px; background:#FAF7F2; border-radius:8px; border:1px solid #E2DDD6;'>
    <strong style='font-size:12px; color:#4A5568;'>Category Key: </strong>
    {legend_html}
    &nbsp;&nbsp;
    <span style='font-size:11px; color:#718096;'>🟣 = Special Needs Group Activity</span>
  </div>

  <!-- Footer -->
  <div style='text-align:center; margin-top:12px; color:#A0AEC0; font-size:11px;'>
    Printed {date.today().strftime("%B %d, %Y")} · ActivityPro Senior Care Calendar · activitypro.app
  </div>
</body>
</html>"""


def build_resident_report_html(resident, engagements, facility_name="ActivityPro Facility"):
    """Build a printable resident participation report."""
    total = len(engagements)
    engaged_count = sum(1 for e in engagements if e['engaged'])
    rate = int(engaged_count / total * 100) if total else 0
    avg_rating = round(sum(e.get('rating') or 0 for e in engagements) / total, 1) if total else 0
    avg_mood_b = round(sum(e.get('mood_before') or 3 for e in engagements) / total, 1) if total else 3
    avg_mood_a = round(sum(e.get('mood_after') or 3 for e in engagements) / total, 1) if total else 3

    rows = ""
    for eng in engagements:
        engaged_icon = "✅ Engaged" if eng['engaged'] else "❌ Not Engaged"
        stars = "⭐" * (eng.get('rating') or 0) or "—"
        note = eng.get('staff_note') or "—"
        rows += f"""
        <tr style='border-bottom:1px solid #F0EDE8;'>
            <td style='padding:8px 12px; font-size:12px;'>{eng['event_date']}</td>
            <td style='padding:8px 12px; font-size:12px; font-weight:600;'>{eng['event_title']}</td>
            <td style='padding:8px 12px; font-size:12px; text-align:center;'>{engaged_icon}</td>
            <td style='padding:8px 12px; font-size:12px; text-align:center;'>{stars}</td>
            <td style='padding:8px 12px; font-size:12px; color:#718096;'>{note}</td>
        </tr>"""

    bar_color = "#7C9A7E" if rate >= 70 else "#D4A843" if rate >= 40 else "#C47B5A"
    disabilities = resident.get('disabilities') or 'None'
    interests = resident.get('special_needs') or '—'
    notes = resident.get('notes') or '—'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Resident Report — {resident['name']}</title>
<style>
  @page {{ size: portrait; margin: 0.75in; }}
  @media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
  body {{ font-family: Georgia, serif; background: white; margin: 0; color: #1A2332; }}
</style>
</head>
<body>
  <div style='text-align:center; padding:20px 0 16px; border-bottom:2px solid #4A6B4C;'>
    <div style='font-size:24px;'>🌸</div>
    <h1 style='margin:8px 0 4px; font-size:20px; font-weight:400;'>{facility_name}</h1>
    <p style='margin:0; color:#718096; font-size:13px;'>Resident Participation Report · Generated {date.today().strftime("%B %d, %Y")}</p>
  </div>

  <div style='margin:20px 0; padding:16px; background:#F5F9F5; border-radius:8px;'>
    <h2 style='margin:0 0 12px; font-size:18px;'>{resident['name']}</h2>
    <table style='width:100%; font-size:13px;'>
      <tr>
        <td style='padding:3px 0; color:#718096; width:30%;'>Room:</td><td style='padding:3px 0;'>{resident.get('room','?')}</td>
        <td style='padding:3px 0; color:#718096; width:30%;'>Age:</td><td style='padding:3px 0;'>{resident.get('age','?')}</td>
      </tr>
      <tr>
        <td style='padding:3px 0; color:#718096;'>Mobility:</td><td>{resident.get('mobility','?').title()}</td>
        <td style='padding:3px 0; color:#718096;'>Cognitive:</td><td>{resident.get('cognitive','?').replace('_',' ').title()}</td>
      </tr>
      <tr>
        <td style='padding:3px 0; color:#718096;'>Disabilities:</td><td colspan='3'>{disabilities}</td>
      </tr>
      <tr>
        <td style='padding:3px 0; color:#718096;'>Interests:</td><td colspan='3'>{interests}</td>
      </tr>
      <tr>
        <td style='padding:3px 0; color:#718096;'>Staff Notes:</td><td colspan='3'>{notes}</td>
      </tr>
    </table>
  </div>

  <div style='display:flex; gap:16px; margin-bottom:20px;'>
    <div style='flex:1; text-align:center; padding:16px; border:1px solid #E2DDD6; border-radius:8px;'>
      <div style='font-size:28px; font-weight:700; color:{bar_color};'>{rate}%</div>
      <div style='font-size:11px; color:#718096; text-transform:uppercase; letter-spacing:1px;'>Engagement Rate</div>
    </div>
    <div style='flex:1; text-align:center; padding:16px; border:1px solid #E2DDD6; border-radius:8px;'>
      <div style='font-size:28px; font-weight:700; color:#4A6B4C;'>{total}</div>
      <div style='font-size:11px; color:#718096; text-transform:uppercase; letter-spacing:1px;'>Sessions Recorded</div>
    </div>
    <div style='flex:1; text-align:center; padding:16px; border:1px solid #E2DDD6; border-radius:8px;'>
      <div style='font-size:28px; font-weight:700; color:#9B8EC4;'>{avg_rating}⭐</div>
      <div style='font-size:11px; color:#718096; text-transform:uppercase; letter-spacing:1px;'>Avg Activity Rating</div>
    </div>
    <div style='flex:1; text-align:center; padding:16px; border:1px solid #E2DDD6; border-radius:8px;'>
      <div style='font-size:28px; font-weight:700; color:#6BA3BE;'>{avg_mood_b}→{avg_mood_a}</div>
      <div style='font-size:11px; color:#718096; text-transform:uppercase; letter-spacing:1px;'>Avg Mood Shift</div>
    </div>
  </div>

  <h3 style='font-size:15px; margin-bottom:12px;'>Activity Participation Log</h3>
  <table style='width:100%; border-collapse:collapse; font-size:13px;'>
    <thead>
      <tr style='background:#F5F9F5;'>
        <th style='padding:10px 12px; text-align:left; font-weight:600;'>Date</th>
        <th style='padding:10px 12px; text-align:left; font-weight:600;'>Activity</th>
        <th style='padding:10px 12px; text-align:center; font-weight:600;'>Engagement</th>
        <th style='padding:10px 12px; text-align:center; font-weight:600;'>Rating</th>
        <th style='padding:10px 12px; text-align:left; font-weight:600;'>Staff Note</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div style='margin-top:24px; padding:16px; background:#F5F9F5; border-radius:8px; font-size:13px;'>
    <strong>Care Plan Summary:</strong><br>
    {resident['name']} has attended {total} activity sessions with a {rate}% engagement rate.
    Average mood shift per session: {avg_mood_b} → {avg_mood_a} ({'positive' if avg_mood_a > avg_mood_b else 'stable' if avg_mood_a == avg_mood_b else 'needs attention'}).
    Disabilities on record: {disabilities}.
    {'Recommend continued participation with disability-appropriate adaptations.' if disabilities and disabilities != 'None' else 'No special adaptations currently required.'}
  </div>

  <div style='text-align:center; margin-top:16px; color:#A0AEC0; font-size:11px; border-top:1px solid #E2DDD6; padding-top:12px;'>
    ActivityPro · {facility_name} · Confidential Resident Record
  </div>
</body>
</html>"""


def build_resident_report_pdf(resident: dict, engagements: list, facility_name: str = "ActivityPro Facility") -> bytes:
    """
    Generate a clinical-grade resident participation report as a PDF (bytes).
    Requires reportlab. Falls back to None if not installed.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()
    sage   = colors.HexColor("#4A6B4C")
    navy   = colors.HexColor("#2C3E50")
    gray   = colors.HexColor("#718096")
    light  = colors.HexColor("#F5F9F5")
    border = colors.HexColor("#E2DDD6")

    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, textColor=navy,
                         spaceAfter=4, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, textColor=sage,
                         spaceAfter=4, fontName="Helvetica-Bold")
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10,
                           textColor=colors.HexColor("#1A2332"), leading=14)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9,
                            textColor=gray, leading=12)
    centered = ParagraphStyle("centered", parent=styles["Normal"], fontSize=10,
                               alignment=TA_CENTER, textColor=gray)

    total   = len(engagements)
    engaged = sum(1 for e in engagements if e['engaged'])
    rate    = int(engaged / total * 100) if total else 0
    avg_r   = round(sum(e.get('rating') or 0 for e in engagements) / total, 1) if total else 0
    avg_mb  = round(sum(e.get('mood_before') or 3 for e in engagements) / total, 1) if total else 3
    avg_ma  = round(sum(e.get('mood_after')  or 3 for e in engagements) / total, 1) if total else 3
    disabilities = resident.get('disabilities') or 'None'
    interests    = resident.get('special_needs') or '—'
    res_notes    = resident.get('notes') or '—'

    story = []

    # ── Header ──
    story.append(Paragraph(f"🌸  {facility_name}", h1))
    story.append(Paragraph(f"Resident Participation Report · Generated {date.today().strftime('%B %d, %Y')}",
                            small))
    story.append(HRFlowable(width="100%", thickness=2, color=sage, spaceAfter=12))

    # ── Resident info ──
    story.append(Paragraph(resident['name'], h2))
    info_data = [
        ["Room:", str(resident.get('room','?')),   "Age:", str(resident.get('age','?'))],
        ["Mobility:", resident.get('mobility','?').title(),
         "Cognitive:", resident.get('cognitive','?').replace('_',' ').title()],
        ["Dietary:", resident.get('dietary','') or 'None',  "", ""],
        ["Disabilities:", disabilities, "", ""],
        ["Interests:", interests, "", ""],
        ["Staff Notes:", res_notes, "", ""],
    ]
    info_table = Table(info_data, colWidths=[1.1*inch, 2.5*inch, 1.1*inch, 2.5*inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), light),
        ("TEXTCOLOR",  (0,0), (0,-1), gray),
        ("TEXTCOLOR",  (2,0), (2,-1), gray),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",   (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWPADDING", (0,0), (-1,-1), 4),
        ("GRID",       (0,0), (-1,-1), 0.25, border),
        ("SPAN",       (1,2), (3,2)),  # dietary spans
        ("SPAN",       (1,3), (3,3)),  # disabilities spans
        ("SPAN",       (1,4), (3,4)),  # interests spans
        ("SPAN",       (1,5), (3,5)),  # notes spans
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.2*inch))

    # ── Summary metrics ──
    bar_color = colors.HexColor("#7C9A7E" if rate >= 70 else "#D4A843" if rate >= 40 else "#C47B5A")
    metrics_data = [
        [f"{rate}%", f"{total}", f"{avg_r}/5 ★", f"{avg_mb}→{avg_ma}"],
        ["Engagement Rate", "Sessions Recorded", "Avg Rating", "Avg Mood Shift"],
    ]
    metrics_table = Table(metrics_data, colWidths=[1.7*inch]*4)
    metrics_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,0), 18),
        ("TEXTCOLOR", (0,0), (0,0), bar_color),
        ("TEXTCOLOR", (1,0), (3,0), sage),
        ("FONTNAME",  (0,1), (-1,1), "Helvetica"),
        ("FONTSIZE",  (0,1), (-1,1), 8),
        ("TEXTCOLOR", (0,1), (-1,1), gray),
        ("ALIGN",     (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",(0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("BOX",       (0,0), (-1,-1), 0.5, border),
        ("INNERGRID", (0,0), (-1,-1), 0.25, border),
        ("BACKGROUND",(0,0), (-1,-1), light),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.2*inch))

    # ── Activity log ──
    story.append(Paragraph("Activity Participation Log", h2))
    if engagements:
        log_header = ["Date", "Activity", "Engaged", "Rating", "Staff Note"]
        log_rows   = [log_header]
        for eng in engagements:
            eng_text  = "✓ Yes" if eng['engaged'] else "✗ No"
            stars     = "★" * (eng.get('rating') or 0) or "—"
            note      = (eng.get('staff_note') or "—")[:60]
            log_rows.append([
                eng['event_date'], eng['event_title'][:35], eng_text, stars, note
            ])
        log_table = Table(log_rows, colWidths=[0.85*inch, 2.1*inch, 0.7*inch, 0.8*inch, 2.25*inch])
        log_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), sage),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("ALIGN",      (2,0), (3,-1), "CENTER"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, light]),
            ("GRID",       (0,0), (-1,-1), 0.25, border),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        story.append(log_table)
    else:
        story.append(Paragraph("No engagement records found.", small))

    story.append(Spacer(1, 0.2*inch))

    # ── Care plan summary ──
    mood_direction = "positive" if avg_ma > avg_mb else "stable" if avg_ma == avg_mb else "declining"
    summary = (
        f"<b>Care Plan Summary:</b> {resident['name']} has attended {total} structured activity "
        f"sessions with a {rate}% engagement rate. Average mood shift per session: "
        f"{avg_mb} → {avg_ma} ({mood_direction}). "
        f"Disabilities on record: {disabilities}. "
        f"{'Recommend continued participation with disability-appropriate adaptations.' if disabilities != 'None' else 'No special adaptations currently required.'}"
    )
    care_para = Paragraph(summary, ParagraphStyle("care", parent=body,
                           backColor=light, borderPadding=10, borderColor=sage,
                           borderWidth=1, leading=15))
    story.append(care_para)

    story.append(Spacer(1, 0.15*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border))
    story.append(Paragraph(f"ActivityPro · {facility_name} · Confidential Resident Record",
                            centered))

    doc.build(story)
    return buf.getvalue()
