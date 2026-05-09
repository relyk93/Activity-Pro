import streamlit as st
from utils.database import (get_events, get_residents, get_activity,
                             get_event_history_for_resident, get_resident_mood_trend)
from datetime import date, timedelta

MOOD_EMOJI = {1: "😔", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}
MOBILITY_ICON = {"independent": "🟢", "cane": "🟡", "walker": "🟡", "wheelchair": "🔴"}

def show():
    st.markdown("# 📋 Session Pre-Brief")
    st.markdown(
        "<div style='color:#718096; margin-bottom:20px;'>"
        "Everything you need before walking into the room — resident reminders, "
        "supplies, and who attended last time."
        "</div>",
        unsafe_allow_html=True
    )

    # ── Event selector ──
    # Pre-select if navigated here from dashboard
    prebriefed_id = st.session_state.pop("prebriefed_event_id", None)

    today = date.today()
    events = get_events(date_from=str(today - timedelta(days=1)),
                        date_to=str(today + timedelta(days=7)))

    if not events:
        st.info("No upcoming events in the next 7 days. Add activities to the calendar first.")
        return

    event_options = {f"{ev['date']} — {ev['title']}": ev for ev in events}
    default_idx = 0
    if prebriefed_id:
        for i, ev in enumerate(events):
            if ev['id'] == prebriefed_id:
                default_idx = i
                break

    selected_label = st.selectbox("Select upcoming activity", list(event_options.keys()),
                                   index=default_idx)
    ev = event_options[selected_label]

    cat = ev.get('category', 'social')
    is_special = ev.get('group_type') == 'special_needs'

    st.markdown(f"""
    <div class='ap-card {"ap-card-lavender" if is_special else "ap-card-sage"}'>
        <div style='font-family: Playfair Display,serif; font-size:1.3rem; font-weight:700; color:#1A2332;'>
            {'🟣 ' if is_special else ''}{ev['title']}
        </div>
        <div style='color:#718096; font-size:0.88rem; margin-top:6px;'>
            📅 {ev['date']} &nbsp;·&nbsp; 🕐 {ev.get('time','TBD')}
            &nbsp;·&nbsp; 📍 {ev.get('location','Activity Room')}
            &nbsp;·&nbsp; <span class='tag tag-{cat}'>{cat.title()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Activity instructions & supplies ──
    activity = get_activity(ev.get('activity_id')) if ev.get('activity_id') else None

    col_inst, col_sup = st.columns(2)
    with col_inst:
        st.markdown("#### 📝 Instructions")
        if activity and activity.get('instructions'):
            for line in activity['instructions'].split('\n'):
                if line.strip():
                    st.markdown(f"- {line.strip()}")
        elif ev.get('notes'):
            st.markdown(ev['notes'])
        else:
            st.markdown("<span style='color:#A0AEC0;'>No instructions on file.</span>",
                        unsafe_allow_html=True)

    with col_sup:
        st.markdown("#### 🛒 Supplies Needed")
        if activity and activity.get('supplies'):
            for item in activity['supplies'].split(','):
                if item.strip():
                    st.markdown(f"- {item.strip()}")
        else:
            st.markdown("<span style='color:#A0AEC0;'>No supplies listed.</span>",
                        unsafe_allow_html=True)
        if activity and activity.get('cost_estimate'):
            st.markdown(f"**Estimated cost:** {activity['cost_estimate']}")

    st.markdown("---")

    # ── Resident attendee list ──
    residents = get_residents()
    if is_special:
        residents = [r for r in residents if r.get('disabilities')]

    st.markdown(f"### 👥 Attendees ({len(residents)} {'residents' if len(residents) != 1 else 'resident'})")
    st.markdown(
        "<div style='color:#A0AEC0; font-size:0.82rem; margin-bottom:16px;'>"
        "Last attendance history shown where available. Green = engaged last time, red = didn't engage."
        "</div>",
        unsafe_allow_html=True
    )

    for r in residents:
        mob_icon = MOBILITY_ICON.get(r.get('mobility','independent'), '⚪')
        disabilities = [d.strip() for d in (r.get('disabilities') or '').split(',') if d.strip()]
        disab_html = " ".join(
            f"<span class='tag tag-mindful' style='font-size:0.7rem;'>{d.replace('_',' ').title()}</span>"
            for d in disabilities
        ) if disabilities else ""

        # Last time at this specific activity
        history = get_event_history_for_resident(r['id'], ev['title'])
        if history:
            engaged_last = history.get('engaged', False)
            mood_b = history.get('mood_before')
            mood_a = history.get('mood_after')
            last_note = history.get('staff_note') or ''
            hist_color = "#7C9A7E" if engaged_last else "#C47B5A"
            hist_icon  = "✅" if engaged_last else "❌"
            mood_str   = f"Mood: {MOOD_EMOJI.get(mood_b,'?')} → {MOOD_EMOJI.get(mood_a,'?')}" if mood_b and mood_a else ""
            hist_html  = f"""
            <div style='background:{"#F5F9F5" if engaged_last else "#FBF0EA"};
                        border-left:3px solid {hist_color};
                        border-radius:6px; padding:6px 10px; margin-top:6px; font-size:0.8rem;'>
                <strong style='color:{hist_color};'>{hist_icon} Last time:</strong>
                {history['event_date']} &nbsp; {mood_str}
                {"<br><em style='color:#718096;'>" + last_note + "</em>" if last_note else ""}
            </div>"""
        else:
            hist_html = """
            <div style='font-size:0.78rem; color:#A0AEC0; margin-top:4px;'>
                First time at this activity
            </div>"""

        # Current mood trend (last 3)
        trend = get_resident_mood_trend(r['id'], limit=3)
        trend_html = " ".join(MOOD_EMOJI.get(t['mood_after'], "😐") for t in trend) if trend else "—"

        notes = r.get('notes') or ''
        dietary = r.get('dietary') or ''

        st.markdown(f"""
        <div style='background:#FFFDF9; border:1px solid #E2DDD6; border-radius:14px;
                    padding:16px 18px; margin-bottom:10px;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                <div>
                    <strong style='font-size:1rem; color:#1A2332;'>{mob_icon} {r['name']}</strong>
                    <span style='color:#A0AEC0; font-size:0.8rem;'> · Rm {r.get('room','?')} · Age {r.get('age','?')}</span>
                    <div style='margin-top:5px;'>{disab_html}</div>
                </div>
                <div style='text-align:right; font-size:1.1rem; letter-spacing:2px;'
                     title='Recent mood trend'>{trend_html}</div>
            </div>
            {"<div style='font-size:0.82rem; color:#4A5568; margin-top:6px;'>💬 " + notes + "</div>" if notes else ""}
            {"<div style='font-size:0.8rem; background:#FBF0EA; border-radius:6px; padding:4px 10px; display:inline-block; margin-top:6px; color:#7A3A1A;'>🍽️ " + dietary + "</div>" if dietary else ""}
            {hist_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Print button ──
    st.markdown("---")
    if st.button("🖨️ Print This Pre-Brief", use_container_width=True):
        _print_prebrief(ev, residents, activity)

def _print_prebrief(ev: dict, residents: list, activity: dict | None):
    """Generate a printable HTML pre-brief sheet."""
    import base64
    rows = ""
    for r in residents:
        history = get_event_history_for_resident(r['id'], ev['title'])
        disabilities = (r.get('disabilities') or '').replace(',', ', ')
        last_str = "First time" if not history else (
            f"{'Engaged' if history['engaged'] else 'Did not engage'} on {history['event_date']}"
        )
        rows += f"""
        <tr>
            <td style='padding:8px 12px; border-bottom:1px solid #F0EDE8;'>{r['name']}</td>
            <td style='padding:8px 12px; border-bottom:1px solid #F0EDE8;'>Rm {r.get('room','?')}</td>
            <td style='padding:8px 12px; border-bottom:1px solid #F0EDE8;'>{r.get('mobility','?').title()}</td>
            <td style='padding:8px 12px; border-bottom:1px solid #F0EDE8; font-size:11px;'>{disabilities or '—'}</td>
            <td style='padding:8px 12px; border-bottom:1px solid #F0EDE8; font-size:11px; color:#718096;'>{last_str}</td>
            <td style='padding:8px 12px; border-bottom:1px solid #F0EDE8; width:80px;'></td>
        </tr>"""

    supplies_html = ""
    if activity and activity.get('supplies'):
        for item in activity['supplies'].split(','):
            if item.strip():
                supplies_html += f"<li>{item.strip()}</li>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Pre-Brief: {ev['title']}</title>
<style>
  @page {{ size: portrait; margin: 0.75in; }}
  @media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
  body {{ font-family: Georgia, serif; color: #1A2332; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ background:#4A6B4C; color:white; padding:10px 12px; text-align:left; font-size:12px; }}
</style>
</head>
<body>
  <div style='border-bottom:2px solid #4A6B4C; padding-bottom:12px; margin-bottom:16px;'>
    <h1 style='margin:0; font-size:20px; color:#1A2332;'>📋 Session Pre-Brief</h1>
    <h2 style='margin:4px 0 0; font-size:16px; color:#4A6B4C; font-weight:400;'>{ev['title']}</h2>
    <p style='margin:4px 0 0; color:#718096; font-size:13px;'>
      {ev['date']} · {ev.get('time','TBD')} · {ev.get('location','Activity Room')}
    </p>
  </div>

  {'<div style="margin-bottom:16px;"><strong>Supplies:</strong><ul style="margin:6px 0;">' + supplies_html + '</ul></div>' if supplies_html else ''}

  <table>
    <thead>
      <tr>
        <th>Resident</th><th>Room</th><th>Mobility</th>
        <th>Conditions</th><th>Last Time Here</th><th>✓ Attended</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div style='margin-top:20px; padding:12px; background:#F5F9F5; border-radius:8px; font-size:12px;'>
    <strong>Staff reminder:</strong> Use the Rate Activities page after the session to log attendance and mood. 🌸
  </div>
  <p style='text-align:center; color:#A0AEC0; font-size:11px; margin-top:16px;'>
    ActivityPro · Printed {date.today().strftime('%B %d, %Y')}
  </p>
</body>
</html>"""

    b64 = base64.b64encode(html.encode()).decode()
    filename = f"PreBrief_{ev['title'].replace(' ','_')}_{ev['date']}.html"
    st.markdown(f"""
    <div class='ap-card ap-card-sage' style='text-align:center; padding:20px;'>
        <a href="data:text/html;base64,{b64}" download="{filename}"
           style='background:#4A6B4C; color:white; padding:10px 24px; border-radius:8px;
                  text-decoration:none; font-weight:600; display:inline-block;'>
            ⬇️ Download Pre-Brief Sheet
        </a>
        <div style='color:#718096; font-size:0.82rem; margin-top:8px;'>
            Open in browser · Ctrl+P / Cmd+P to print
        </div>
    </div>
    """, unsafe_allow_html=True)
