import streamlit as st
from utils.database import get_residents, get_last_activity, get_resident_mood_trend, get_engagements
from datetime import date

MOOD_EMOJI    = {1: "😔", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}
MOBILITY_ICON = {
    "independent": ("🟢", "Independent"),
    "cane":        ("🟡", "Uses Cane"),
    "walker":      ("🟡", "Uses Walker"),
    "wheelchair":  ("🔴", "Wheelchair"),
}

DEMO_CARDS = [
    {
        "name": "Margaret Thompson", "room": "101", "age": 78,
        "mobility": "walker", "disabilities": "Arthritis",
        "special_needs": "Gardening, flower arranging, morning walks",
        "notes": "Very social — loves chatting with other residents during activities.",
        "dietary": "",
    },
    {
        "name": "Robert 'Bob' Jenkins", "room": "102", "age": 82,
        "mobility": "cane", "disabilities": "Hearing Loss, Diabetic",
        "special_needs": "Sports, trivia, history",
        "notes": "Sit him near the front during group activities. Prefers mornings.",
        "dietary": "Diabetic-friendly meals only",
    },
]


def _mood_dots(trend: list) -> str:
    if not trend:
        return "<span style='color:var(--ap-text-light); font-size:0.8rem;'>No mood data yet</span>"
    dots = []
    for entry in trend:
        m     = entry['mood_after']
        emoji = MOOD_EMOJI.get(m, "😐")
        d     = entry['date']                          # avoid backslash in f-string (Python < 3.12)
        dots.append(f"<span title='{d}'>{emoji}</span>")
    return " ".join(dots)


def _days_since(date_str: str) -> int:
    try:
        return (date.today() - date.fromisoformat(date_str)).days
    except Exception:
        return 999


def show():
    st.markdown("# 👤 Resident Quick Cards")
    st.markdown(
        "<div style='color:var(--ap-text-light); margin-bottom:20px;'>"
        "Everything you need to know about each resident — at a glance, before you walk into the room."
        "</div>",
        unsafe_allow_html=True,
    )

    residents = get_residents()

    if not residents:
        # ── Demo preview when no residents are loaded ──
        st.info(
            "No residents added yet. Here's a preview of what resident cards look like "
            "once you add your residents.",
            icon="👀",
        )
        st.markdown("#### Example Cards")
        cols = st.columns(2)
        for col, r in zip(cols, DEMO_CARDS):
            with col:
                _render_card(r, demo=True)
        st.markdown("---")
        if st.button("➕ Go to Residents to add your first resident", type="primary"):
            st.session_state.page = "Residents"
            st.rerun()
        return

    # ── Filter bar ──
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search = st.text_input("Search by name", placeholder="e.g. Margaret",
                               label_visibility="collapsed")
    with col_filter:
        show_at_risk = st.checkbox("⚠️ At-risk only")

    if search:
        residents = [r for r in residents if search.lower() in r['name'].lower()]

    if show_at_risk:
        from utils.database import get_at_risk_residents, get_declining_mood_residents
        at_risk_ids   = {r['id'] for r in get_at_risk_residents()}
        declining_ids = {r['id'] for r in get_declining_mood_residents()}
        flagged       = at_risk_ids | declining_ids
        residents     = [r for r in residents if r['id'] in flagged]

    if not residents:
        st.info("No residents match your filter.")
        return

    # ── Cards grid: 2 per row ──
    for i in range(0, len(residents), 2):
        cols = st.columns(2)
        for col, r in zip(cols, residents[i:i+2]):
            with col:
                _render_card(r)


def _render_card(r: dict, demo: bool = False):
    mob_icon, mob_label = MOBILITY_ICON.get(r.get('mobility', 'independent'), ("⚪", "Unknown"))

    if demo:
        last_activity_str = "Morning Chair Yoga · Today"
        days_ago          = 0
        eng_rate          = 85
        mood_dots         = "🙂 😊 😐 🙂 😊"
        total_sessions    = 12
    else:
        last = get_last_activity(r['id'])
        trend = get_resident_mood_trend(r['id'], limit=5)
        mood_dots = _mood_dots(trend)

        engs           = get_engagements(resident_id=r['id'])
        total_sessions = len(engs)
        engaged        = sum(1 for e in engs if e['engaged'])
        eng_rate       = int(engaged / total_sessions * 100) if total_sessions else None

        if last:
            days_ago = _days_since(last['event_date'])
            if days_ago == 0:
                last_label = "Today"
            elif days_ago == 1:
                last_label = "Yesterday"
            else:
                last_label = f"{days_ago} days ago"
            last_activity_str = f"{last['event_title']} · {last_label}"
        else:
            last_activity_str = "No activity recorded yet"
            days_ago          = 999

    alert      = not demo and days_ago >= 14
    alert_html = (
        "<div style='font-size:0.75rem; color:var(--ap-accent); font-weight:600; margin-bottom:6px;'>"
        "⚠️ No engagement in 14+ days</div>"
    ) if alert else ""

    demo_banner = (
        "<div style='font-size:0.72rem; background:var(--ap-primary-light); color:var(--ap-primary); "
        "font-weight:600; border-radius:6px; padding:3px 8px; display:inline-block; margin-bottom:8px;'>"
        "📋 Example Card</div>"
    ) if demo else ""

    disabilities = [d.strip() for d in (r.get('disabilities') or '').split(',') if d.strip()]
    disab_html   = " ".join(
        f"<span class='tag tag-mindful'>{d.replace('_',' ').title()}</span>"
        for d in disabilities
    ) if disabilities else "<span style='color:var(--ap-text-light); font-size:0.8rem;'>None on record</span>"

    if eng_rate is None:
        bar_color = "var(--ap-border)"
        rate_str  = "No data"
    else:
        bar_color = "#7C9A7E" if eng_rate >= 70 else "#D4A843" if eng_rate >= 40 else "#C47B5A"
        rate_str  = f"{eng_rate}%"

    border_color = "var(--ap-accent)" if alert else "var(--ap-border)"

    dietary_html = ""
    if r.get("dietary"):
        dietary_html = (
            "<div style='background:var(--ap-accent-light); border-radius:8px; padding:8px 12px; "
            "margin-top:10px; font-size:0.8rem; color:var(--ap-text-mid);'>"
            f"<strong>Dietary:</strong> {r['dietary']}</div>"
        )

    sessions_label = f"{total_sessions} session{'s' if total_sessions != 1 else ''}" if not demo else "12 sessions"

    st.markdown(f"""
    <div style='background:var(--ap-surface); border-radius:16px; border:1.5px solid {border_color};
                box-shadow:0 2px 10px var(--ap-shadow); padding:20px; margin-bottom:16px;'>

        {demo_banner}
        {alert_html}

        <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>
            <div>
                <div style='font-family:Playfair Display,serif; font-size:1.1rem; font-weight:700;
                            color:var(--ap-text);'>{r['name']}</div>
                <div style='color:var(--ap-text-light); font-size:0.8rem; margin-top:2px;'>
                    Rm {r.get('room','?')} &nbsp;·&nbsp; Age {r.get('age','?')}
                </div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:1.4rem;'>{mob_icon}</div>
                <div style='font-size:0.72rem; color:var(--ap-text-light);'>{mob_label}</div>
            </div>
        </div>

        <div style='margin-bottom:10px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;'>
                Conditions / Disabilities
            </div>
            {disab_html}
        </div>

        <div style='margin-bottom:10px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:2px;'>
                Interests
            </div>
            <div style='font-size:0.85rem; color:var(--ap-text-mid);'>
                {r.get('special_needs','') or '—'}
            </div>
        </div>

        <div style='margin-bottom:10px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:2px;'>
                Staff Notes
            </div>
            <div style='font-size:0.82rem; color:var(--ap-text-mid); font-style:italic;'>
                {r.get('notes','') or '—'}
            </div>
        </div>

        <div style='margin-bottom:10px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;'>
                Mood Trend (last 5 sessions)
            </div>
            <div style='font-size:1.3rem; letter-spacing:4px;'>{mood_dots}</div>
        </div>

        <div style='border-top:1px solid var(--ap-border); margin-top:12px; padding-top:12px;
                    display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                            text-transform:uppercase; letter-spacing:0.06em;'>Last Activity</div>
                <div style='font-size:0.82rem; color:var(--ap-text-mid);'>{last_activity_str}</div>
                <div style='font-size:0.72rem; color:var(--ap-text-light);'>{sessions_label} total</div>
            </div>
            <div style='text-align:right;'>
                <div style='font-weight:700; color:{bar_color}; font-size:1.1rem;'>{rate_str}</div>
                <div style='font-size:0.72rem; color:var(--ap-text-light);'>Engagement</div>
            </div>
        </div>

        {dietary_html}
    </div>
    """, unsafe_allow_html=True)
