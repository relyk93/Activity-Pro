import streamlit as st
from utils.database import get_events, get_subscription
from utils.pdf_export import build_weekly_calendar_html, build_resident_report_html
from utils.database import get_residents, get_engagements
from datetime import date, timedelta
import base64

def show():
    st.markdown("# 🖨️ Print & Export")
    st.markdown("<div style='color:#718096; margin-bottom:20px;'>Generate printable calendars and resident reports — perfect for posting on the wall or including in care plans.</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📅 Weekly Wall Calendar", "📋 Resident Report"])

    # ─── Tab 1: Weekly Calendar ───
    with tab1:
        st.markdown("### Print Weekly Activity Calendar")
        st.markdown("Generates a **landscape PDF-ready** calendar you can print and post on the activity board.")

        col1, col2 = st.columns(2)
        with col1:
            if "print_week_start" not in st.session_state:
                today = date.today()
                st.session_state.print_week_start = today - timedelta(days=today.weekday())
            week_start = st.date_input("Week to print",
                value=st.session_state.print_week_start,
                key="print_week_picker")
            # Snap to Monday
            week_start = week_start - timedelta(days=week_start.weekday())
        with col2:
            sub = get_subscription()
            facility_name = sub.get('facility_name', 'My Facility')
            st.info(f"📍 Facility: **{facility_name}**\nChange in Settings if needed.")

        week_end = week_start + timedelta(days=6)
        events = get_events(date_from=str(week_start), date_to=str(week_end))

        st.markdown(f"**Preview:** Week of {week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')} · {len(events)} activities scheduled")

        if st.button("🖨️ Generate Printable Calendar", type="primary", use_container_width=True):
            html = build_weekly_calendar_html(events, week_start, facility_name)
            b64 = base64.b64encode(html.encode()).decode()
            filename = f"ActivityPro_Calendar_{week_start.strftime('%Y-%m-%d')}.html"

            st.markdown(f"""
            <div class='ap-card ap-card-sage' style='text-align:center; padding:32px;'>
                <div style='font-size:2.5rem; margin-bottom:12px;'>✅</div>
                <div style='font-size:1.1rem; font-weight:600; margin-bottom:8px;'>Your calendar is ready!</div>
                <div style='color:#718096; margin-bottom:20px; font-size:0.9rem;'>
                    Click the download button below, open the file in your browser, then use <strong>File → Print</strong> (or Ctrl+P / Cmd+P).<br>
                    Set orientation to <strong>Landscape</strong> for best results.
                </div>
                <a href="data:text/html;base64,{b64}" download="{filename}"
                   style='background:#4A6B4C; color:white; padding:12px 28px; border-radius:10px;
                          text-decoration:none; font-weight:600; font-size:1rem; display:inline-block;'>
                    ⬇️ Download Calendar
                </a>
            </div>
            """, unsafe_allow_html=True)

        # Mini preview
        if events:
            st.markdown("#### Schedule Preview")
            days = [week_start + timedelta(days=i) for i in range(7)]
            preview_cols = st.columns(7)
            events_by_date = {}
            for ev in events:
                d = ev['date']
                if d not in events_by_date:
                    events_by_date[d] = []
                events_by_date[d].append(ev)

            for col, day in zip(preview_cols, days):
                with col:
                    is_today = day == date.today()
                    bg = "#4A6B4C" if is_today else "#2C3E50"
                    st.markdown(f"""
                    <div style='background:{bg}; color:white; border-radius:8px; padding:6px; text-align:center; margin-bottom:6px;'>
                        <div style='font-size:0.65rem; opacity:0.8;'>{day.strftime("%a").upper()}</div>
                        <div style='font-size:1.1rem; font-weight:700;'>{day.day}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    day_evs = events_by_date.get(str(day), [])
                    for ev in day_evs:
                        cat = ev.get('category','social')
                        cat_colors = {"physical":"#DEF0DE","mindful":"#EBE4F5","social":"#DDE8F5","cognitive":"#F5EDDD","creative":"#FBF0EA"}
                        bg_c = cat_colors.get(cat, "#F5F5F5")
                        st.markdown(f"""
                        <div style='background:{bg_c}; border-radius:5px; padding:4px 6px; margin-bottom:4px; font-size:0.65rem; font-weight:600;'>
                            {ev.get('time','')} {ev['title'][:18]}{'...' if len(ev['title'])>18 else ''}
                        </div>
                        """, unsafe_allow_html=True)
                    if not day_evs:
                        st.markdown("<div style='color:#A0AEC0; font-size:0.65rem; text-align:center;'>—</div>", unsafe_allow_html=True)
        else:
            st.info("No activities scheduled for this week. Use the AI Generator or Calendar to add activities first.")

    # ─── Tab 2: Resident Report ───
    with tab2:
        st.markdown("### Print Resident Participation Report")
        st.markdown("Generates a **care-plan-ready** PDF report for any resident — great for family meetings and medical documentation.")

        residents = get_residents()
        if not residents:
            st.info("No residents found. Add residents first.")
            return

        resident_map = {r['name']: r for r in residents}
        selected_name = st.selectbox("Select Resident", list(resident_map.keys()))
        resident = resident_map[selected_name]

        engs = get_engagements(resident_id=resident['id'])
        sub = get_subscription()
        facility_name = sub.get('facility_name', 'My Facility')

        col1, col2, col3 = st.columns(3)
        with col1:
            total = len(engs)
            st.markdown(f"""<div class='metric-box'><div class='metric-number'>{total}</div><div class='metric-label'>Sessions</div></div>""", unsafe_allow_html=True)
        with col2:
            engaged = sum(1 for e in engs if e['engaged'])
            rate = int(engaged/total*100) if total else 0
            st.markdown(f"""<div class='metric-box'><div class='metric-number'>{rate}%</div><div class='metric-label'>Engaged</div></div>""", unsafe_allow_html=True)
        with col3:
            avg_r = round(sum(e.get('rating') or 0 for e in engs)/total,1) if total else 0
            st.markdown(f"""<div class='metric-box'><div class='metric-number'>{avg_r}⭐</div><div class='metric-label'>Avg Rating</div></div>""", unsafe_allow_html=True)

        if st.button(f"🖨️ Generate Report for {selected_name}", type="primary", use_container_width=True):
            html = build_resident_report_html(resident, engs, facility_name)
            b64 = base64.b64encode(html.encode()).decode()
            safe_name = selected_name.replace(' ', '_')
            filename = f"ActivityPro_Report_{safe_name}_{date.today().strftime('%Y-%m-%d')}.html"

            st.markdown(f"""
            <div class='ap-card ap-card-sage' style='text-align:center; padding:32px;'>
                <div style='font-size:2.5rem; margin-bottom:12px;'>✅</div>
                <div style='font-size:1.1rem; font-weight:600; margin-bottom:8px;'>Report ready for {selected_name}!</div>
                <div style='color:#718096; margin-bottom:20px; font-size:0.9rem;'>
                    Download, open in browser, then print with <strong>Ctrl+P / Cmd+P</strong>.<br>
                    This report is suitable for care plan documentation and family sharing.
                </div>
                <a href="data:text/html;base64,{b64}" download="{filename}"
                   style='background:#4A6B4C; color:white; padding:12px 28px; border-radius:10px;
                          text-decoration:none; font-weight:600; font-size:1rem; display:inline-block;'>
                    ⬇️ Download Report
                </a>
            </div>
            """, unsafe_allow_html=True)

        if not engs:
            st.warning(f"No engagement records found for {selected_name}. Rate some activities first to populate the report.")
