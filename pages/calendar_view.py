import streamlit as st
from utils.database import get_events, get_activities, save_event, delete_event, get_activity
from datetime import date, timedelta
import calendar


def _parse_supplies(events):
    """Return (by_day, consolidated) from a list of DB event dicts."""
    skip = {"none", "none needed", "nothing", "n/a", ""}
    by_day = {}
    consolidated = {}
    for ev in events:
        items = [
            s.strip() for s in (ev.get("supplies") or "").split(",")
            if s.strip().lower() not in skip
        ]
        if not items:
            continue
        d = ev["date"]
        if d not in by_day:
            by_day[d] = []
        by_day[d].append({"title": ev["title"], "supplies": items})
        for item in items:
            key = item.lower()
            if key not in consolidated:
                consolidated[key] = {"display": item, "activities": []}
            consolidated[key]["activities"].append(ev["title"])
    return sorted(by_day.items()), consolidated


def _supply_csv(by_day_sorted, period_label):
    rows = [f"Supply List — {period_label}", "Date,Activity,Supply Item"]
    for d, acts in by_day_sorted:
        for act in acts:
            for s in act["supplies"]:
                rows.append(f"{d},{act['title']},{s}")
    return "\n".join(rows)


def _monthly_calendar_html(month_events, month_start):
    """Printable HTML: month grid + day-by-day schedule with per-activity supplies."""
    import calendar as _cal
    import streamlit as _st

    month_label = month_start.strftime("%B %Y")
    facility_name = _st.session_state.get("facility_name", "") or ""
    program_name = _st.session_state.get("program_name", "") or ""
    days_in_month = _cal.monthrange(month_start.year, month_start.month)[1]

    # Build events lookup by date string
    ev_by_date = {}
    for ev in month_events:
        d = ev["date"]
        if d not in ev_by_date:
            ev_by_date[d] = []
        ev_by_date[d].append(ev)

    cat_bg = {
        "physical": "#DEF0DE", "mindful": "#EBE4F5", "social": "#DDE8F5",
        "cognitive": "#F5EDDD", "creative": "#FBF0EA",
    }

    # ── Month grid ──
    first_weekday = month_start.weekday()  # 0=Mon
    grid_html = "<table class='cal-grid'><thead><tr>"
    for h in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        grid_html += f"<th>{h}</th>"
    grid_html += "</tr></thead><tbody><tr>"

    # Leading empty cells
    for _ in range(first_weekday):
        grid_html += "<td></td>"

    for day_num in range(1, days_in_month + 1):
        d = date(month_start.year, month_start.month, day_num)
        day_str = d.isoformat()
        day_events = ev_by_date.get(day_str, [])

        acts_html = ""
        for ev in day_events:
            bg = cat_bg.get(ev.get("category", "social"), "#F5F5F5")
            acts_html += (
                f"<div style='background:{bg};border-radius:3px;padding:2px 4px;"
                f"margin:2px 0;font-size:0.68rem;'>"
                f"{ev.get('time','')[:5] if ev.get('time') else ''} {ev['title']}</div>"
            )

        is_today = d == date.today()
        day_bg = "#0F766E" if is_today else "transparent"
        day_color = "white" if is_today else "#1A2332"
        grid_html += (
            f"<td><div style='background:{day_bg};color:{day_color};border-radius:4px;"
            f"width:22px;height:22px;display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:0.82rem;margin-bottom:4px;'>{day_num}</div>"
            f"{acts_html}</td>"
        )

        # New row after Sunday
        if d.weekday() == 6 and day_num < days_in_month:
            grid_html += "</tr><tr>"

    # Trailing empty cells
    last_weekday = date(month_start.year, month_start.month, days_in_month).weekday()
    for _ in range(6 - last_weekday):
        grid_html += "<td></td>"
    grid_html += "</tr></tbody></table>"

    # ── Day-by-day schedule with supplies ──
    schedule_html = ""
    for day_num in range(1, days_in_month + 1):
        d = date(month_start.year, month_start.month, day_num)
        day_str = d.isoformat()
        day_events = ev_by_date.get(day_str, [])
        if not day_events:
            continue

        schedule_html += (
            f"<div class='day-block'>"
            f"<div class='day-header'>{d.strftime('%A, %B %d')}</div>"
        )
        for ev in sorted(day_events, key=lambda e: e.get("time", "")):
            bg = cat_bg.get(ev.get("category", "social"), "#F5F5F5")
            supplies = (ev.get("supplies") or "None").strip()
            schedule_html += (
                f"<div class='act-block' style='border-left:4px solid {bg};'>"
                f"<div class='act-title'>{ev.get('time', '')} &nbsp; {ev['title']}</div>"
                f"<div class='act-meta'>"
                f"⏱ {ev.get('duration_minutes', 60)} min &nbsp;|&nbsp; "
                f"📍 {ev.get('location', 'Activity Room')} &nbsp;|&nbsp; "
                f"💰 {ev.get('cost_estimate', 'Free')}</div>"
                f"<div class='act-supplies'>🛒 <strong>Supplies:</strong> {supplies}</div>"
            )
            if ev.get("description"):
                schedule_html += f"<div class='act-desc'>{ev['description']}</div>"
            schedule_html += "</div>"
        schedule_html += "</div>"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  body{{font-family:Arial,sans-serif;max-width:960px;margin:32px auto;padding:32px;
       color:#1A2332;background:#FFFDF9;}}
  h1{{color:#0F766E;font-size:1.8rem;margin-bottom:4px;}}
  h2{{color:#2D6A4F;font-size:1.2rem;border-bottom:2px solid #0F766E;
      padding-bottom:6px;margin-top:40px;}}
  .cal-grid{{width:100%;border-collapse:collapse;margin-bottom:40px;}}
  .cal-grid th{{background:#0F766E;color:white;padding:8px;text-align:center;
               font-size:0.85rem;}}
  .cal-grid td{{border:1px solid #E2DDD6;padding:6px;vertical-align:top;
               min-width:100px;min-height:80px;font-size:0.78rem;}}
  .day-block{{margin-bottom:28px;page-break-inside:avoid;}}
  .day-header{{background:#0F766E;color:white;padding:8px 14px;border-radius:6px;
              font-weight:700;font-size:1rem;margin-bottom:8px;}}
  .act-block{{padding:10px 14px;margin-bottom:8px;border-radius:0 8px 8px 0;
             background:#F8FAFC;border:1px solid #E2DDD6;}}
  .act-title{{font-weight:700;font-size:0.95rem;margin-bottom:4px;}}
  .act-meta{{font-size:0.8rem;color:#718096;margin-bottom:4px;}}
  .act-supplies{{font-size:0.82rem;color:#2D6A4F;margin-bottom:4px;}}
  .act-desc{{font-size:0.82rem;color:#4A5568;font-style:italic;}}
  .footer{{margin-top:48px;text-align:center;color:#94A3B8;font-size:0.75rem;}}
  @media print{{
    body{{margin:0;padding:16px;}}
    h2{{page-break-before:always;}}
    .day-block{{page-break-inside:avoid;}}
  }}
</style></head><body>
<h1>📅 {month_label} Activity Calendar</h1>
{f"<p style='font-size:1.1rem;font-weight:700;color:#1A2332;margin:0;'>{facility_name}</p>" if facility_name else ""}
{f"<p style='color:#2D6A4F;margin:2px 0 20px;'>{program_name}</p>" if program_name else ""}
<p style='color:#718096;margin-bottom:24px;'>Generated by ActivityPro</p>
<h2>Monthly Overview</h2>
{grid_html}
<h2>Daily Schedule &amp; Supplies</h2>
{schedule_html if schedule_html else "<p style='color:#718096;'>No activities scheduled this month.</p>"}
<div class='footer'>ActivityPro &nbsp;·&nbsp; {date.today().strftime('%B %d, %Y')}</div>
</body></html>"""


def _daily_flyer_html(day_events, flyer_date):
    """Print-ready daily activity flyer — large fonts, color-coded, works on colored paper."""
    facility_name = st.session_state.get("facility_name", "") or ""
    program_name  = st.session_state.get("program_name", "") or ""

    cat_style = {
        "physical":  ("#DEF0DE", "#3A6B3A", "#4CAF50"),
        "mindful":   ("#EBE4F5", "#5A3A7F", "#9B59B6"),
        "social":    ("#DDE8F5", "#2A4A7F", "#3498DB"),
        "cognitive": ("#F5EDDD", "#7F5A2A", "#E67E22"),
        "creative":  ("#FBF0EA", "#7F3A1A", "#E74C3C"),
    }

    acts_html = ""
    for ev in sorted(day_events, key=lambda e: e.get("time", "")):
        cat = ev.get("category", "social")
        bg, fg, border = cat_style.get(cat, ("#F5F5F5", "#333333", "#999999"))
        time_raw   = ev.get("time", "")
        parts      = time_raw.split(" ")
        time_num   = parts[0] if parts else time_raw
        time_ampm  = parts[1] if len(parts) > 1 else ""
        desc       = ev.get("description", "")
        location   = ev.get("location", "Activity Room")
        cost       = ev.get("cost_estimate", "Free")
        dur        = ev.get("duration_minutes", 60)
        special    = " &nbsp;|&nbsp; 🟣 Special Needs Group" if ev.get("group_type") == "special_needs" else ""
        desc_block = f"<div class='act-desc'>{desc}</div>" if desc else ""
        acts_html += f"""
<div class='act' style='background:{bg};border-left-color:{border};'>
  <div class='act-time' style='color:{fg};'>{time_num}<span class='ampm'>{time_ampm}</span></div>
  <div class='act-body'>
    <div class='act-name' style='color:{fg};'>{ev['title']}</div>
    <div class='act-meta'>📍 {location} &nbsp;|&nbsp; ⏱ {dur} min &nbsp;|&nbsp; 💰 {cost}{special}</div>
    {desc_block}
  </div>
</div>"""

    facility_block = f"<div class='fac-name'>{facility_name}</div>" if facility_name else ""
    program_block  = f"<div class='prog-name'>{program_name}</div>" if program_name else ""
    empty          = "<p style='color:#94A3B8;font-size:16pt;text-align:center;padding:48px 0;'>No activities scheduled for this day.</p>"
    footer_fac     = f"{facility_name} &nbsp;·&nbsp; " if facility_name else ""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:Calibri,Arial,sans-serif;max-width:8.5in;min-height:11in;
        margin:0 auto;padding:0.45in;background:#fff;color:#1A2332;}}
  .header{{background:linear-gradient(135deg,#0F766E 0%,#2D6A4F 100%);
           color:white;padding:28px 36px;border-radius:16px;
           margin-bottom:28px;text-align:center;}}
  .fac-name{{font-size:20pt;font-weight:700;letter-spacing:0.04em;margin-bottom:3px;}}
  .prog-name{{font-size:13pt;opacity:0.85;margin-bottom:12px;}}
  .dow{{font-size:24pt;font-weight:300;letter-spacing:0.12em;
        text-transform:uppercase;opacity:0.88;margin-bottom:2px;}}
  .date-big{{font-size:54pt;font-weight:900;line-height:1.05;}}
  .yr{{font-size:17pt;font-weight:300;opacity:0.76;margin-top:2px;}}
  .section-title{{font-size:16pt;font-weight:700;color:#0F766E;
                  text-transform:uppercase;letter-spacing:0.08em;
                  border-bottom:3px solid #0F766E;padding-bottom:6px;
                  margin:0 0 14px 0;}}
  .act{{display:flex;align-items:flex-start;gap:18px;padding:16px 18px;
        margin-bottom:10px;border-radius:12px;border-left:8px solid;
        page-break-inside:avoid;}}
  .act-time{{font-size:22pt;font-weight:900;min-width:105px;
             line-height:1.1;text-align:center;white-space:nowrap;}}
  .ampm{{font-size:11pt;font-weight:400;display:block;}}
  .act-body{{flex:1;}}
  .act-name{{font-size:26pt;font-weight:700;line-height:1.1;margin-bottom:5px;}}
  .act-meta{{font-size:12pt;color:#718096;}}
  .act-desc{{font-size:12pt;color:#4A5568;font-style:italic;margin-top:5px;}}
  .footer{{margin-top:32px;text-align:center;color:#94A3B8;font-size:9pt;
           border-top:1px solid #E2DDD6;padding-top:12px;}}
  @media print{{
    body{{padding:0.35in;}}
    @page{{size:letter portrait;margin:0.25in;}}
  }}
</style></head><body>
<div class='header'>
  {facility_block}{program_block}
  <div class='dow'>{flyer_date.strftime("%A")}</div>
  <div class='date-big'>{flyer_date.strftime("%B")} {flyer_date.day}</div>
  <div class='yr'>{flyer_date.year}</div>
</div>
<div class='section-title'>Today's Activities</div>
{acts_html if day_events else empty}
<div class='footer'>{footer_fac}Generated by ActivityPro &nbsp;·&nbsp; {date.today().strftime('%B %d, %Y')}</div>
</body></html>"""


def _supply_html(by_day_sorted, consolidated, period_label):
    rows_html = ""
    for d, acts in by_day_sorted:
        rows_html += f"<h3 style='color:#0F766E;margin-top:24px;'>{d}</h3><ul>"
        for act in acts:
            rows_html += f"<li><strong>{act['title']}</strong>: {', '.join(act['supplies'])}</li>"
        rows_html += "</ul>"

    consol_html = "<ul>"
    for key in sorted(consolidated):
        v = consolidated[key]
        acts_str = ", ".join(sorted(set(v["activities"])))
        consol_html += f"<li><strong>{v['display']}</strong> — for: {acts_str}</li>"
    consol_html += "</ul>"

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  body{{font-family:Georgia,serif;max-width:700px;margin:40px auto;padding:40px;color:#1A2332;background:#FFFDF9;}}
  h1{{color:#0F766E;}} h2{{color:#2D6A4F;border-bottom:1px solid #ccc;padding-bottom:6px;}}
  h3{{color:#0F766E;margin-top:20px;}} ul{{line-height:2;}}
  .footer{{margin-top:48px;color:#94A3B8;font-size:0.78rem;text-align:center;}}
  @media print{{body{{margin:0;padding:20px;}}}}
</style></head><body>
<h1>🛒 Supply List</h1>
<p style='color:#718096;'>{period_label}</p>
<h2>By Day</h2>{rows_html}
<h2>Consolidated Shopping List</h2>{consol_html}
<div class='footer'>Generated by ActivityPro</div>
</body></html>"""

def show():
    st.markdown("# 📅 Activity Calendar")

    # Week navigation
    if "cal_week_start" not in st.session_state:
        today = date.today()
        st.session_state.cal_week_start = today - timedelta(days=today.weekday())

    week_start = st.session_state.cal_week_start
    week_end = week_start + timedelta(days=6)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Previous Week"):
            st.session_state.cal_week_start -= timedelta(days=7)
            st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align:center; margin:0;'>{week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("Next Week →"):
            st.session_state.cal_week_start += timedelta(days=7)
            st.rerun()

    # ── Month download buttons ──
    month_start = week_start.replace(day=1)
    days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]
    month_end = month_start + timedelta(days=days_in_month - 1)
    month_label = month_start.strftime("%B %Y")
    month_events = get_events(date_from=str(month_start), date_to=str(month_end))

    dl_c1, dl_c2 = st.columns(2)
    with dl_c1:
        cal_html = _monthly_calendar_html(month_events, month_start)
        st.download_button(
            f"📥 Download {month_label} Calendar",
            data=cal_html,
            file_name=f"calendar_{month_label.replace(' ','_')}.html",
            mime="text/html",
            use_container_width=True,
            help="Opens in browser — File → Print → Save as PDF",
        )
    with dl_c2:
        by_day_sorted_m, consolidated_m = _parse_supplies(month_events)
        supply_html_m = _supply_html(by_day_sorted_m, consolidated_m, month_label)
        st.download_button(
            f"🛒 Download {month_label} Supply List",
            data=supply_html_m,
            file_name=f"supplies_{month_label.replace(' ','_')}.html",
            mime="text/html",
            use_container_width=True,
            help="Opens in browser — File → Print → Save as PDF",
        )

    st.markdown("---")

    # ── Daily Flyer Generator ──
    with st.expander("🖨 Daily Activity Flyer", expanded=True):
        flyer_date = st.date_input(
            "Generate flyer for",
            value=date.today(),
            key="flyer_date_picker",
        )
        flyer_events = get_events(date_from=str(flyer_date), date_to=str(flyer_date))
        if flyer_events:
            st.caption(f"{len(flyer_events)} {'activity' if len(flyer_events) == 1 else 'activities'} on {flyer_date.strftime('%A, %B %d')} — ready to print.")
        else:
            st.caption(f"No activities scheduled for {flyer_date.strftime('%A, %B %d')} yet. Generate a calendar first.")
        flyer_html = _daily_flyer_html(flyer_events, flyer_date)
        st.download_button(
            f"📄 Download Flyer — {flyer_date.strftime('%A, %B %d')}",
            data=flyer_html,
            file_name=f"flyer_{flyer_date.isoformat()}.html",
            mime="text/html",
            use_container_width=True,
            help="Open the downloaded file in any browser → File → Print. Looks great on coloured paper!",
        )

    st.markdown("---")

    # Get events for this week
    events = get_events(date_from=str(week_start), date_to=str(week_end))
    events_by_date = {}
    for ev in events:
        d = ev['date']
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(ev)

    # Calendar grid
    days = [week_start + timedelta(days=i) for i in range(7)]
    cols = st.columns(7)

    cat_colors = {
        "physical": ("#DEF0DE", "#3A6B3A"),
        "mindful": ("#EBE4F5", "#5A3A7F"),
        "social": ("#DDE8F5", "#2A4A7F"),
        "cognitive": ("#F5EDDD", "#7F5A2A"),
        "creative": ("#FBF0EA", "#7F3A1A"),
        "special_needs": ("#F0EDF8", "#4A3A6B"),
    }

    for i, (col, day) in enumerate(zip(cols, days)):
        with col:
            is_today = day == date.today()
            day_bg = "#7C9A7E" if is_today else "#FFFDF9"
            day_color = "white" if is_today else "#1A2332"
            st.markdown(f"""
            <div style='background:{day_bg}; border-radius:10px; padding:8px; text-align:center; margin-bottom:8px;'>
                <div style='font-size:0.75rem; color:{"#D4F5D4" if is_today else "#718096"}; text-transform:uppercase; letter-spacing:0.1em;'>{day.strftime("%a")}</div>
                <div style='font-size:1.3rem; font-weight:700; color:{day_color};'>{day.day}</div>
            </div>
            """, unsafe_allow_html=True)

            day_str = str(day)
            day_events = events_by_date.get(day_str, [])

            for ev in day_events:
                cat = ev.get('category', 'social')
                bg, fg = cat_colors.get(cat, ("#F5F5F5", "#333"))
                is_special = ev.get('group_type') == 'special_needs'
                border = "2px solid #9B8EC4" if is_special else "none"
                st.markdown(f"""
                <div style='background:{bg}; color:{fg}; border-radius:8px; padding:6px 8px; margin-bottom:6px; font-size:0.75rem; font-weight:600; border:{border}; cursor:pointer;'>
                    {'🟣 ' if is_special else ''}{ev.get('time','?')} {ev['title']}
                </div>
                """, unsafe_allow_html=True)
                if st.button("View", key=f"view_{ev['id']}", use_container_width=True):
                    st.session_state.selected_event = ev
                    st.session_state.show_event_modal = True

            if st.button("+ Add", key=f"add_{day_str}", use_container_width=True):
                st.session_state.add_event_date = day_str
                st.session_state.show_add_event = True

    st.markdown("---")

    # Legend
    st.markdown("""
    <div style='display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px;'>
        <span class='tag tag-physical'>Physical</span>
        <span class='tag tag-mindful'>Mindful</span>
        <span class='tag tag-social'>Social</span>
        <span class='tag tag-cognitive'>Cognitive</span>
        <span class='tag tag-creative'>Creative</span>
        <span style='background:#F0EDF8; color:#4A3A6B; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; border:2px solid #9B8EC4;'>🟣 Special Needs</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Supply List ──
    st.markdown("---")
    st.markdown("### 🛒 Supply List")

    supply_mode = st.radio(
        "Show supplies for",
        ["This Week", "This Month"],
        horizontal=True,
        key="supply_mode",
    )

    if supply_mode == "This Month":
        month_start = week_start.replace(day=1)
        import calendar as _cal
        days_in_month = _cal.monthrange(month_start.year, month_start.month)[1]
        month_end = month_start + timedelta(days=days_in_month - 1)
        supply_events = get_events(date_from=str(month_start), date_to=str(month_end))
        period_label = month_start.strftime("%B %Y")
    else:
        supply_events = events
        period_label = f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}"

    by_day_sorted, consolidated = _parse_supplies(supply_events)

    if not by_day_sorted:
        st.caption("No supplies needed for this period — or no activities scheduled yet.")
    else:
        total_items = sum(len(v["activities"]) for v in consolidated.values())
        st.caption(f"{len(consolidated)} unique supply items across {len(by_day_sorted)} days")

        view_tab, list_tab = st.tabs(["📅 By Day", "🗒 Shopping List"])

        with view_tab:
            for d, acts in by_day_sorted:
                try:
                    from datetime import date as _date
                    label = _date.fromisoformat(d).strftime("%A, %B %d")
                except Exception:
                    label = d
                with st.expander(label, expanded=False):
                    for act in acts:
                        st.markdown(f"**{act['title']}**")
                        for s in act["supplies"]:
                            st.markdown(f"- {s}")

        with list_tab:
            st.caption("Alphabetical — deduplicated across all activities")
            for key in sorted(consolidated):
                v = consolidated[key]
                acts_str = " · ".join(sorted(set(v["activities"])))
                st.markdown(f"**{v['display']}** — _{acts_str}_")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "📥 Download CSV",
                data=_supply_csv(by_day_sorted, period_label),
                file_name=f"supplies_{period_label.replace(' ','_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "🖨 Download / Print",
                data=_supply_html(by_day_sorted, consolidated, period_label),
                file_name=f"supplies_{period_label.replace(' ','_')}.html",
                mime="text/html",
                use_container_width=True,
                help="Open in browser → File → Print → Save as PDF",
            )

    st.markdown("---")

    # Event detail panel
    if st.session_state.get("show_event_modal") and st.session_state.get("selected_event"):
        ev = st.session_state.selected_event
        st.markdown("---")
        st.markdown("## 📋 Activity Details")

        col_a, col_b = st.columns([2, 1])
        with col_a:
            cat = ev.get('category', 'social')
            bg, fg = cat_colors.get(cat, ("#F5F5F5", "#333"))
            is_special = ev.get('group_type') == 'special_needs'
            st.markdown(f"""
            <div class='ap-card'>
                <div style='display:flex; gap:10px; align-items:center; margin-bottom:16px;'>
                    <span class='tag tag-{cat}'>{cat.title()}</span>
                    {'<span style="background:#EBE4F5;color:#5A3A7F;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;border:1px solid #9B8EC4;">🟣 Special Needs Group</span>' if is_special else '<span style="background:#DEF0DE;color:#3A6B3A;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">👥 All Residents</span>'}
                </div>
                <h2 style='margin:0 0 8px 0;'>{ev['title']}</h2>
                <div style='color:#718096; margin-bottom:16px;'>📅 {ev['date']} &nbsp;|&nbsp; 🕐 {ev.get('time','TBD')} &nbsp;|&nbsp; 📍 {ev.get('location','Activity Room')} &nbsp;|&nbsp; ⏱ {ev.get('duration_minutes', 60)} min &nbsp;|&nbsp; 💰 {ev.get('cost_estimate','Free')}</div>
            </div>
            """, unsafe_allow_html=True)

            if ev.get('instructions'):
                st.markdown("#### 📝 Step-by-Step Instructions")
                st.markdown(f"""<div class='ap-card ap-card-sage'><pre style='font-family: DM Sans, sans-serif; white-space: pre-wrap; color:#1A2332; margin:0;'>{ev['instructions']}</pre></div>""", unsafe_allow_html=True)

            if ev.get('supplies'):
                st.markdown("#### 🛒 Supplies Needed")
                st.markdown(f"""<div class='ap-card ap-card-terra'>{ev['supplies']}</div>""", unsafe_allow_html=True)

            if ev.get('disability_friendly'):
                st.markdown("#### ♿ Accessibility Notes")
                disability_labels = {
                    "wheelchair": "♿ Wheelchair accessible",
                    "dementia": "🧠 Dementia-friendly",
                    "hearing_loss": "👂 Hearing loss adaptations",
                    "vision_impairment": "👁 Vision impairment adaptations",
                    "limited_mobility": "🦾 Limited mobility friendly",
                    "arthritis": "🤲 Arthritis-friendly",
                    "anxiety": "💚 Anxiety-sensitive",
                    "parkinson": "🫀 Parkinson's adaptations",
                }
                tags = ""
                for d in ev['disability_friendly'].split(','):
                    d = d.strip()
                    label = disability_labels.get(d, d.title())
                    tags += f"<span class='tag tag-mindful' style='margin:3px;'>{label}</span>"
                st.markdown(f"<div class='ap-card ap-card-lavender'>{tags}</div>", unsafe_allow_html=True)

            if ev.get('notes'):
                st.markdown(f"**Staff Notes:** {ev['notes']}")

        with col_b:
            st.markdown("#### Actions")
            if st.button("⭐ Rate This Activity", use_container_width=True):
                st.session_state.rate_event_id = ev['id']
                st.session_state.page = "Rate Activities"
                st.rerun()
            if st.button("✏️ Edit Event", use_container_width=True):
                st.session_state.edit_event = ev
                st.session_state.show_add_event = True
            if st.button("🗑 Delete Event", use_container_width=True):
                delete_event(ev['id'])
                st.session_state.show_event_modal = False
                st.success("Event deleted.")
                st.rerun()
            if st.button("✕ Close", use_container_width=True):
                st.session_state.show_event_modal = False
                st.rerun()

    # Add Event Panel
    if st.session_state.get("show_add_event"):
        st.markdown("---")
        st.markdown("## ➕ Add Event to Calendar")
        activities = get_activities()
        activity_options = {a['title']: a['id'] for a in activities}

        with st.form("add_event_form"):
            event_date = st.date_input("Date", value=date.fromisoformat(st.session_state.get("add_event_date", str(date.today()))))
            event_time = st.text_input("Time (e.g. 10:00 AM)", value="10:00 AM")
            selected_activity = st.selectbox("Select Activity", list(activity_options.keys()))
            location = st.text_input("Location", value="Activity Room")
            group_type = st.radio("Group", ["all", "special_needs"], format_func=lambda x: "All Residents" if x == "all" else "Special Needs Group")
            notes = st.text_area("Notes (optional)")

            col_s, col_c = st.columns(2)
            submitted = col_s.form_submit_button("Add to Calendar", use_container_width=True)
            cancelled = col_c.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                act_id = activity_options[selected_activity]
                save_event({
                    "activity_id": act_id,
                    "title": selected_activity,
                    "date": str(event_date),
                    "time": event_time,
                    "location": location,
                    "group_type": group_type,
                    "notes": notes,
                })
                st.session_state.show_add_event = False
                st.success(f"✅ '{selected_activity}' added to {event_date.strftime('%B %d')}!")
                st.rerun()
            if cancelled:
                st.session_state.show_add_event = False
                st.rerun()
