import streamlit as st
from utils.database import (get_residents, get_last_activity,
                             get_resident_mood_trend, get_engagements)
from utils.database import get_at_risk_residents, get_declining_mood_residents
from datetime import date

MOOD_EMOJI    = {1: "😔", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}
MOOD_LABEL    = {1: "Very Low", 2: "Low", 3: "Neutral", 4: "Good", 5: "Great"}
MOBILITY_ICON = {
    "independent": ("🟢", "Independent"),
    "cane":        ("🟡", "Uses Cane"),
    "walker":      ("🟡", "Uses Walker"),
    "wheelchair":  ("🔴", "Wheelchair"),
}
COGNITIVE_COLOR = {
    "intact":       "var(--ap-primary)",
    "mild":         "#D4A843",
    "moderate":     "var(--ap-accent)",
    "severe":       "#E53E3E",
}


def _days_since(date_str: str) -> int:
    try:
        return (date.today() - date.fromisoformat(date_str)).days
    except Exception:
        return 999


def _mood_bar(trend: list) -> str:
    if not trend:
        return "<span style='color:var(--ap-text-light); font-size:0.85rem;'>No mood data yet</span>"
    dots = []
    for entry in trend:
        m     = entry.get('mood_after') or 3
        emoji = MOOD_EMOJI.get(m, "😐")
        d     = entry.get('date', '')
        label = MOOD_LABEL.get(m, '')
        dots.append(f"<span title='{d} — {label}' style='font-size:1.4rem;'>{emoji}</span>")
    return "<span style='letter-spacing:6px;'>" + "".join(dots) + "</span>"


def _eng_bar(rate: int | None) -> str:
    if rate is None:
        return "<span style='color:var(--ap-text-light); font-size:0.85rem;'>No data yet</span>"
    color = "#7C9A7E" if rate >= 70 else "#D4A843" if rate >= 40 else "#C47B5A"
    return f"""
    <div style='display:flex; align-items:center; gap:10px;'>
        <div style='flex:1; background:var(--ap-surface-2); border-radius:99px; height:10px; overflow:hidden;'>
            <div style='width:{rate}%; background:{color}; height:100%; border-radius:99px;'></div>
        </div>
        <span style='font-weight:700; color:{color}; font-size:1rem; min-width:38px;'>{rate}%</span>
    </div>"""


def show():
    st.markdown("# 👤 Resident Quick Cards")
    st.markdown(
        "<div style='color:var(--ap-text-light); margin-bottom:20px;'>"
        "Full at-a-glance profile for any resident — care details, interests, "
        "mood trend, and recent activity history in one place."
        "</div>",
        unsafe_allow_html=True,
    )

    residents = get_residents()

    if not residents:
        st.info("No residents added yet.", icon="👀")
        if st.button("➕ Add Residents", type="primary"):
            st.session_state.page = "Residents"
            st.rerun()
        return

    # ── Resident selector with prev / next navigation ──
    names = [r['name'] for r in residents]
    r_map = {r['name']: r for r in residents}

    # Initialise index in session state
    if "rc_index" not in st.session_state:
        st.session_state.rc_index = 0
    st.session_state.rc_index = min(st.session_state.rc_index, len(residents) - 1)

    sel_col, prev_col, next_col = st.columns([6, 1, 1])
    with sel_col:
        chosen_name = st.selectbox(
            "Select resident",
            names,
            index=st.session_state.rc_index,
            key="rc_dropdown",
            label_visibility="collapsed",
        )
        st.session_state.rc_index = names.index(chosen_name)
    with prev_col:
        if st.button("◀ Prev", use_container_width=True,
                     disabled=st.session_state.rc_index == 0):
            st.session_state.rc_index -= 1
            st.rerun()
    with next_col:
        if st.button("Next ▶", use_container_width=True,
                     disabled=st.session_state.rc_index == len(residents) - 1):
            st.session_state.rc_index += 1
            st.rerun()

    r = residents[st.session_state.rc_index]

    # ── Fetch data ──
    at_risk_ids   = {x['id'] for x in get_at_risk_residents()}
    declining_ids = {x['id'] for x in get_declining_mood_residents()}
    last          = get_last_activity(r['id'])
    trend         = get_resident_mood_trend(r['id'], limit=8)
    engs          = get_engagements(resident_id=r['id'])

    total_sessions = len(engs)
    engaged_count  = sum(1 for e in engs if e['engaged'])
    eng_rate       = int(engaged_count / total_sessions * 100) if total_sessions else None

    if last:
        days_ago   = _days_since(last['event_date'])
        last_label = (
            "Today" if days_ago == 0 else
            "Yesterday" if days_ago == 1 else
            f"{days_ago} days ago"
        )
        last_str = f"{last['event_title']} · {last_label}"
    else:
        days_ago = 999
        last_str = "No activity recorded yet"

    is_at_risk   = r['id'] in at_risk_ids
    is_declining = r['id'] in declining_ids

    mob_icon, mob_label = MOBILITY_ICON.get(r.get('mobility', 'independent'), ("⚪", "Unknown"))
    cog_level  = (r.get('cognitive') or 'intact').lower()
    cog_color  = COGNITIVE_COLOR.get(cog_level, "var(--ap-text-light)")
    disabilities = [d.strip() for d in (r.get('disabilities') or '').split(',') if d.strip()]
    interests    = [i.strip() for i in (r.get('special_needs') or '').split(',') if i.strip()]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Alert banners ──
    if is_at_risk:
        st.markdown("""
        <div style='background:linear-gradient(135deg,#FBF0EA,#FEF5F0);
                    border-left:4px solid var(--ap-accent); border-radius:10px;
                    padding:12px 18px; margin-bottom:12px;'>
            <strong style='color:var(--ap-accent);'>⚠️ Engagement Alert</strong>
            <span style='color:var(--ap-text-mid); font-size:0.9rem; margin-left:8px;'>
                This resident has not engaged with an activity in 14+ days.
            </span>
        </div>
        """, unsafe_allow_html=True)
    if is_declining:
        st.markdown("""
        <div style='background:linear-gradient(135deg,#FBF0EA,#FEF5F0);
                    border-left:4px solid #E53E3E; border-radius:10px;
                    padding:12px 18px; margin-bottom:12px;'>
            <strong style='color:#E53E3E;'>📉 Declining Mood</strong>
            <span style='color:var(--ap-text-mid); font-size:0.9rem; margin-left:8px;'>
                Mood scores have been trending downward recently.
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ── Main card ──
    left, right = st.columns([3, 2])

    with left:
        # Header
        st.markdown(f"""
        <div class='ap-card' style='padding:24px; margin-bottom:16px;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                <div>
                    <div style='font-family:Playfair Display,serif; font-size:1.6rem;
                                font-weight:700; color:var(--ap-text); line-height:1.2;'>
                        {r['name']}
                    </div>
                    <div style='color:var(--ap-text-light); font-size:0.9rem; margin-top:4px;'>
                        Room {r.get('room','—')} &nbsp;·&nbsp; Age {r.get('age','—')}
                        {(' &nbsp;·&nbsp; 🎂 ' + r['birthday']) if r.get('birthday') else ''}
                    </div>
                </div>
                <div style='text-align:center; min-width:64px;'>
                    <div style='font-size:2rem;'>{mob_icon}</div>
                    <div style='font-size:0.75rem; color:var(--ap-text-light); margin-top:2px;'>
                        {mob_label}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Care profile
        disab_tags = " ".join(
            f"<span class='tag tag-mindful'>{d}</span>" for d in disabilities
        ) if disabilities else "<span style='color:var(--ap-text-light);'>None recorded</span>"

        interest_tags = " ".join(
            f"<span class='tag tag-social'>{i}</span>" for i in interests
        ) if interests else "<span style='color:var(--ap-text-light);'>None recorded</span>"

        st.markdown(f"""
        <div class='ap-card ap-card-sky' style='margin-bottom:16px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:12px;'>
                Care Profile
            </div>

            <div style='margin-bottom:10px;'>
                <div style='font-size:0.8rem; font-weight:600; color:var(--ap-text-mid);
                            margin-bottom:4px;'>Conditions &amp; Disabilities</div>
                <div>{disab_tags}</div>
            </div>

            <div style='margin-bottom:10px;'>
                <div style='font-size:0.8rem; font-weight:600; color:var(--ap-text-mid);
                            margin-bottom:2px;'>Cognitive Status</div>
                <div style='font-size:0.9rem; color:{cog_color}; font-weight:600;'>
                    {cog_level.title()}
                </div>
            </div>

            <div>
                <div style='font-size:0.8rem; font-weight:600; color:var(--ap-text-mid);
                            margin-bottom:2px;'>Dietary Requirements</div>
                <div style='font-size:0.9rem; color:var(--ap-text);'>
                    {r.get('dietary') or '<span style="color:var(--ap-text-light);">None recorded</span>'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Personal
        family_line = ""
        if r.get('family_name') or r.get('family_email'):
            fn = r.get('family_name') or ''
            fe = r.get('family_email') or ''
            family_line = f"""
            <div style='margin-top:10px;'>
                <div style='font-size:0.8rem; font-weight:600; color:var(--ap-text-mid);
                            margin-bottom:2px;'>Family Contact</div>
                <div style='font-size:0.9rem; color:var(--ap-text);'>
                    {fn}{' &nbsp;·&nbsp; ' + fe if fn and fe else fe or fn}
                </div>
            </div>"""

        st.markdown(f"""
        <div class='ap-card ap-card-sage' style='margin-bottom:16px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:12px;'>
                Personal
            </div>

            <div style='margin-bottom:10px;'>
                <div style='font-size:0.8rem; font-weight:600; color:var(--ap-text-mid);
                            margin-bottom:4px;'>Interests &amp; Hobbies</div>
                <div>{interest_tags}</div>
            </div>

            <div>
                <div style='font-size:0.8rem; font-weight:600; color:var(--ap-text-mid);
                            margin-bottom:2px;'>Staff Notes</div>
                <div style='font-size:0.88rem; color:var(--ap-text); font-style:italic;
                            line-height:1.6;'>
                    {r.get('notes') or '<span style="color:var(--ap-text-light); font-style:normal;">No notes recorded</span>'}
                </div>
            </div>
            {family_line}
        </div>
        """, unsafe_allow_html=True)

        # Quick actions
        st.markdown("**Quick Actions**")
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button("📋 Pre-Brief", key="rc_prebrief", use_container_width=True,
                         type="primary"):
                st.session_state.page = "Pre-Brief"
                st.rerun()
        with qa2:
            if st.button("📅 Calendar", key="rc_cal", use_container_width=True):
                st.session_state.page = "Calendar"
                st.rerun()
        with qa3:
            if st.button("👨‍👩‍👧 Family", key="rc_family", use_container_width=True):
                st.session_state.page = "Family Updates"
                st.rerun()

    with right:
        # Engagement stats
        st.markdown(f"""
        <div class='ap-card' style='margin-bottom:16px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:14px;'>
                Engagement
            </div>
            <div style='margin-bottom:12px;'>
                {_eng_bar(eng_rate)}
            </div>
            <div style='display:flex; justify-content:space-between;
                        font-size:0.82rem; color:var(--ap-text-light);'>
                <span>{total_sessions} sessions total</span>
                <span>{engaged_count} engaged</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Mood trend
        st.markdown(f"""
        <div class='ap-card' style='margin-bottom:16px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:10px;'>
                Mood Trend — Last 8 Sessions
            </div>
            <div style='margin-bottom:6px;'>{_mood_bar(trend)}</div>
            <div style='font-size:0.78rem; color:var(--ap-text-light);'>
                😔 Very Low &nbsp; 😐 Neutral &nbsp; 😊 Great
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Last activity
        st.markdown(f"""
        <div class='ap-card' style='margin-bottom:16px;'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:8px;'>
                Last Activity
            </div>
            <div style='font-size:0.92rem; color:var(--ap-text); font-weight:500;'>
                {last_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recent session log
        st.markdown(f"""
        <div class='ap-card'>
            <div style='font-size:0.72rem; color:var(--ap-text-light); font-weight:600;
                        text-transform:uppercase; letter-spacing:0.07em; margin-bottom:10px;'>
                Recent Sessions
            </div>
        """, unsafe_allow_html=True)

        recent = engs[:8]
        if recent:
            rows = ""
            for e in recent:
                icon    = "✅" if e['engaged'] else "❌"
                mood_a  = MOOD_EMOJI.get(e.get('mood_after'), "")
                rating  = "⭐" * (e.get('rating') or 0) if e.get('rating') else ""
                note    = e.get('staff_note') or ""
                note_el = (f"<div style='font-size:0.75rem; color:var(--ap-text-light); "
                           f"font-style:italic; margin-top:1px;'>{note}</div>") if note else ""
                rows += f"""
                <div style='padding:7px 0; border-bottom:1px solid var(--ap-border);
                            display:flex; justify-content:space-between; align-items:flex-start;'>
                    <div>
                        <div style='font-size:0.82rem; color:var(--ap-text);'>
                            {icon} {e['event_date']} — {e['event_title']}
                        </div>
                        {note_el}
                    </div>
                    <div style='font-size:0.82rem; white-space:nowrap; margin-left:8px;'>
                        {mood_a} {rating}
                    </div>
                </div>"""
            st.markdown(rows + "</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<span style='color:var(--ap-text-light); font-size:0.85rem;'>"
                "No sessions recorded yet.</span></div>",
                unsafe_allow_html=True,
            )
