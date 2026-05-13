import streamlit as st
from utils.database import (get_council_meetings, save_council_meeting,
                             update_council_meeting, delete_council_meeting)
from utils.auth import get_current_staff, is_director
from datetime import date

TOPIC_OPTIONS = [
    "Activities & Programming",
    "Food & Dining",
    "Facility & Environment",
    "Staffing & Care",
    "Outings & Events",
    "Safety & Comfort",
    "Suggestions for Improvement",
    "Resident Achievements",
    "Other",
]

TOPIC_COLORS = {
    "Activities & Programming": "var(--ap-primary)",
    "Food & Dining":            "var(--ap-accent)",
    "Facility & Environment":   "#9B8EC4",
    "Staffing & Care":          "#0EA5E9",
    "Outings & Events":         "#10B981",
    "Safety & Comfort":         "#EF4444",
    "Suggestions for Improvement": "var(--ap-primary-dark)",
    "Resident Achievements":    "#F59E0B",
    "Other":                    "var(--ap-text-light)",
}

def _topic_tags(topics_str: str) -> str:
    if not topics_str:
        return ""
    tags_html = ""
    for t in topics_str.split("|"):
        t = t.strip()
        if t:
            color = TOPIC_COLORS.get(t, "var(--ap-text-light)")
            tags_html += f"""<span style='display:inline-block; background:transparent;
                border:1px solid {color}; color:{color};
                border-radius:20px; padding:2px 10px; font-size:0.75rem;
                font-weight:600; margin:2px;'>{t}</span>"""
    return tags_html

def _meeting_form(prefix: str, defaults: dict = None) -> dict | None:
    """Render the meeting form. Returns form data dict on submit, None otherwise."""
    d = defaults or {}
    with st.form(f"council_form_{prefix}", clear_on_submit=False):
        st.markdown("#### Meeting Details")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            meeting_date = st.date_input(
                "Meeting Date",
                value=date.fromisoformat(d.get("meeting_date", date.today().isoformat())),
            )
        with col2:
            title = st.text_input(
                "Meeting Title",
                value=d.get("title", ""),
                placeholder="e.g. May Resident Council Meeting",
            )
        with col3:
            attendee_count = st.number_input(
                "Residents Present",
                min_value=0, max_value=200,
                value=int(d.get("attendee_count", 0)),
            )

        topics = st.multiselect(
            "Topics Discussed",
            options=TOPIC_OPTIONS,
            default=[t for t in (d.get("topics", "") or "").split("|") if t.strip() in TOPIC_OPTIONS],
        )

        st.markdown("#### Meeting Synopsis")
        synopsis = st.text_area(
            "General Summary",
            value=d.get("synopsis", ""),
            height=130,
            placeholder=(
                "Summarise the overall tone and key themes of the meeting. "
                "What did residents want the staff to know?"
            ),
        )

        col_a, col_b = st.columns(2)
        with col_a:
            ideas = st.text_area(
                "💡 Resident Ideas & Suggestions",
                value=d.get("ideas", ""),
                height=120,
                placeholder="• Add a movie night on Fridays\n• Suggest a gardening club\n• Request more music activities",
            )
        with col_b:
            concerns = st.text_area(
                "⚠️ Concerns Raised",
                value=d.get("concerns", ""),
                height=120,
                placeholder="• Hallway temperature too cold\n• Request quieter dining hours\n• Ask about outdoor seating",
            )

        action_items = st.text_area(
            "✅ Action Items & Follow-ups",
            value=d.get("action_items", ""),
            height=100,
            placeholder="• Director to check thermostat settings by Friday\n• Schedule trial movie night for next month\n• Order additional outdoor chairs",
        )

        submitted = st.form_submit_button("💾 Save Meeting Notes", type="primary", use_container_width=True)

    if submitted:
        return {
            "meeting_date":  meeting_date.isoformat(),
            "title":         title or f"Resident Council — {meeting_date.strftime('%B %d, %Y')}",
            "synopsis":      synopsis,
            "ideas":         ideas,
            "concerns":      concerns,
            "action_items":  action_items,
            "topics":        "|".join(topics),
            "attendee_count": attendee_count,
            "recorded_by":   get_current_staff().get("full_name", "Staff"),
        }
    return None


def show():
    st.markdown("# 🏛 Resident Council")
    st.markdown(
        "<div style='color:var(--ap-text-light); margin-bottom:24px;'>"
        "Record meeting synopses, resident ideas, concerns raised, and follow-up action items "
        "from each Resident Society meeting."
        "</div>",
        unsafe_allow_html=True,
    )

    meetings = get_council_meetings()

    # ── New meeting form ──
    with st.expander("➕ Record New Meeting", expanded=len(meetings) == 0):
        data = _meeting_form("new")
        if data:
            save_council_meeting(data)
            st.success("Meeting notes saved!")
            st.rerun()

    if not meetings:
        st.info("No council meetings recorded yet. Use the form above to log your first one.")
        return

    # ── Summary strip ──
    total_meetings  = len(meetings)
    total_ideas     = sum(1 for m in meetings if m.get("ideas"))
    total_actions   = sum(
        len([l for l in (m.get("action_items") or "").splitlines() if l.strip()])
        for m in meetings
    )
    m1, m2, m3 = st.columns(3)
    for col, num, label in [
        (m1, total_meetings, "Meetings Logged"),
        (m2, total_ideas,    "Meetings with Ideas"),
        (m3, total_actions,  "Total Action Items"),
    ]:
        with col:
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-number'>{num}</div>
                <div class='metric-label'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Meeting History")

    # ── Meeting history ──
    for m in meetings:
        topics_html = _topic_tags(m.get("topics", ""))
        attendees = m.get("attendee_count", 0)
        recorded  = m.get("recorded_by", "")
        mid       = m["id"]

        header = (
            f"**{m.get('title') or m['meeting_date']}** "
            f"· {m['meeting_date']}"
            f"{f'  ·  👥 {attendees} residents' if attendees else ''}"
            f"{f'  ·  📝 {recorded}' if recorded else ''}"
        )

        with st.expander(header, expanded=False):

            if topics_html:
                st.markdown(topics_html, unsafe_allow_html=True)
                st.markdown("")

            # Synopsis
            if m.get("synopsis"):
                st.markdown("**Meeting Summary**")
                st.markdown(
                    f"<div class='ap-card' style='padding:14px; font-size:0.92rem; line-height:1.7;'>"
                    f"{m['synopsis'].replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True,
                )

            col_i, col_c = st.columns(2)
            with col_i:
                if m.get("ideas"):
                    st.markdown("**💡 Ideas & Suggestions**")
                    st.markdown(
                        f"<div class='ap-card ap-card-sage' style='padding:14px; font-size:0.88rem; line-height:1.8;'>"
                        f"{m['ideas'].replace(chr(10), '<br>')}</div>",
                        unsafe_allow_html=True,
                    )
            with col_c:
                if m.get("concerns"):
                    st.markdown("**⚠️ Concerns Raised**")
                    st.markdown(
                        f"<div class='ap-card ap-card-terra' style='padding:14px; font-size:0.88rem; line-height:1.8;'>"
                        f"{m['concerns'].replace(chr(10), '<br>')}</div>",
                        unsafe_allow_html=True,
                    )

            if m.get("action_items"):
                st.markdown("**✅ Action Items**")
                items = [l.strip() for l in m["action_items"].splitlines() if l.strip()]
                items_html = "".join(
                    f"<div style='padding:6px 0; border-bottom:1px solid var(--ap-border); "
                    f"font-size:0.88rem;'>☐ {item}</div>"
                    for item in items
                )
                st.markdown(
                    f"<div class='ap-card' style='padding:14px;'>{items_html}</div>",
                    unsafe_allow_html=True,
                )

            # Edit / Delete (director only)
            if is_director():
                st.markdown("")
                edit_col, del_col = st.columns([3, 1])
                with edit_col:
                    if st.button("✏️ Edit This Meeting", key=f"edit_btn_{mid}"):
                        st.session_state[f"editing_{mid}"] = True

                if st.session_state.get(f"editing_{mid}"):
                    updated = _meeting_form(f"edit_{mid}", defaults=dict(m))
                    if updated:
                        update_council_meeting(mid, updated)
                        st.session_state.pop(f"editing_{mid}", None)
                        st.success("Meeting updated!")
                        st.rerun()
                    if st.button("Cancel", key=f"cancel_edit_{mid}"):
                        st.session_state.pop(f"editing_{mid}", None)
                        st.rerun()

                with del_col:
                    if st.button("🗑 Delete", key=f"del_{mid}", type="secondary"):
                        st.session_state[f"confirm_del_{mid}"] = True

                if st.session_state.get(f"confirm_del_{mid}"):
                    st.warning("Delete this meeting record permanently?")
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        if st.button("Yes, delete", key=f"yes_del_{mid}", type="primary"):
                            delete_council_meeting(mid)
                            st.session_state.pop(f"confirm_del_{mid}", None)
                            st.rerun()
                    with no_col:
                        if st.button("Cancel", key=f"no_del_{mid}"):
                            st.session_state.pop(f"confirm_del_{mid}", None)
                            st.rerun()
