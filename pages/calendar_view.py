import streamlit as st
from utils.database import get_events, get_activities, save_event, delete_event, get_activity
from datetime import date, timedelta
import calendar

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
