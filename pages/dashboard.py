import streamlit as st
from utils.database import (get_residents, get_events, get_engagements,
                             get_at_risk_residents, get_declining_mood_residents,
                             get_last_activity, get_subscription)
from utils.email_sender import send_email, build_staff_reminder_html
from utils.auth import get_current_staff, is_director
from datetime import date, timedelta

MOOD_EMOJI    = {1: "😔", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}
MOBILITY_ICON = {"independent": "🟢", "cane": "🟡", "walker": "🟡", "wheelchair": "🔴"}


def show():
    staff      = get_current_staff()
    first_name = (staff.get("full_name") or "Director").split()[0]
    facility   = st.session_state.get("facility_name", "My Facility")
    today      = date.today()
    today_str  = str(today)

    hour     = __import__('datetime').datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

    st.markdown(f"""
    <div style='margin-bottom:24px;'>
        <div style='font-family:Playfair Display,serif; font-size:1.8rem; font-weight:700;
                    color:var(--ap-text);'>
            {greeting}, {first_name}. 👋
        </div>
        <div style='color:var(--ap-text-light); font-size:0.95rem; margin-top:4px;'>
            {today.strftime("%A, %B %d, %Y")} &nbsp;·&nbsp; {facility}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Data ──
    residents    = get_residents()
    today_events = get_events(date_from=today_str, date_to=today_str)
    week_events  = get_events(date_from=today_str, date_to=str(today + timedelta(days=6)))
    all_eng      = get_engagements()
    at_risk      = get_at_risk_residents(days_threshold=14)
    declining    = get_declining_mood_residents()

    engaged_count = sum(1 for e in all_eng if e['engaged'])
    eng_rate      = int(engaged_count / len(all_eng) * 100) if all_eng else 0

    # Low engagement: residents with <40% across all recorded sessions
    low_eng = []
    for r in residents:
        engs = get_engagements(resident_id=r['id'])
        if engs:
            rate = int(sum(1 for e in engs if e['engaged']) / len(engs) * 100)
            if rate < 40:
                low_eng.append((r, rate))

    # ── Alert banner ──
    if at_risk or declining or low_eng:
        parts = []
        if at_risk:
            names = ", ".join(r['name'].split()[0] for r in at_risk[:3])
            extra = f" +{len(at_risk)-3} more" if len(at_risk) > 3 else ""
            parts.append(f"**{len(at_risk)} residents** haven't engaged in 14+ days ({names}{extra})")
        if declining:
            names = ", ".join(r['name'].split()[0] for r in declining[:2])
            parts.append(f"**{len(declining)} residents** show declining mood ({names})")
        if low_eng:
            names = ", ".join(r['name'].split()[0] for r, _ in low_eng[:2])
            parts.append(f"**{len(low_eng)} residents** below 40% engagement ({names})")
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#FBF0EA,#FEF5F0); border:1px solid #C47B5A;
                    border-left:4px solid #C47B5A; border-radius:12px; padding:14px 20px; margin-bottom:20px;'>
            <div style='font-weight:600; color:#7A3A1A; font-size:0.9rem; margin-bottom:4px;'>
                ⚠️ Needs Attention Today
            </div>
            <div style='color:#5A2A0A; font-size:0.85rem;'>{"  ·  ".join(parts)}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Metrics ──
    c1, c2, c3, c4 = st.columns(4)
    for col, num, label in [
        (c1, len(residents),    "Active Residents"),
        (c2, len(today_events), "Activities Today"),
        (c3, len(week_events),  "This Week"),
        (c4, f"{eng_rate}%",    "Engagement Rate"),
    ]:
        with col:
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-number'>{num}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    # ══════════════════════════════════════
    with col_left:

        # ── Today's activities ──
        hdr_col, email_col = st.columns([3, 1])
        with hdr_col:
            st.markdown("### 📅 Today's Activities")
        with email_col:
            if today_events and is_director():
                if st.button("📤 Email to Staff", key="email_staff_dash",
                             use_container_width=True):
                    st.session_state["dash_email_staff"] = True

        if st.session_state.get("dash_email_staff") and is_director():
            with st.form("staff_email_form"):
                staff_addr = st.text_input("Staff email address",
                                           placeholder="staff@facility.com")
                sent = st.form_submit_button("Send Schedule", type="primary")
            if sent:
                if staff_addr:
                    try:
                        smtp_ok = bool(st.secrets.get("SMTP_USER", ""))
                    except Exception:
                        smtp_ok = False
                    if smtp_ok:
                        sub      = get_subscription()
                        fname    = sub.get("facility_name", facility)
                        html_body = build_staff_reminder_html(today_events, fname)
                        subject   = f"Today's Activity Schedule — {today.strftime('%A, %B %d')}"
                        ok, msg   = send_email(staff_addr, subject, html_body)
                        st.success(f"Sent to {staff_addr}") if ok else st.error(msg)
                    else:
                        st.warning("Configure SMTP in Streamlit Cloud secrets to send emails.")
                    st.session_state["dash_email_staff"] = False
                else:
                    st.warning("Enter an email address.")
        cat_class = {
            "physical": "ap-card-sage",   "mindful":   "ap-card-lavender",
            "social":   "ap-card-sky",    "cognitive": "ap-card-terra",
            "creative": "ap-card-terra",
        }
        if today_events:
            for ev in today_events:
                cat   = ev.get('category', 'social')
                card  = cat_class.get(cat, "ap-card")
                badge = "🔵 All Residents" if ev['group_type'] == 'all' else "🟣 Special Needs"
                st.markdown(f"""
                <div class='ap-card {card}'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div>
                            <div style='font-weight:600; font-size:1.05rem; color:var(--ap-text);'>
                                {ev['title']}
                            </div>
                            <div style='color:var(--ap-text-light); font-size:0.85rem; margin-top:4px;'>
                                🕐 {ev.get('time','TBD')} &nbsp;|&nbsp;
                                📍 {ev.get('location','Activity Room')} &nbsp;|&nbsp; {badge}
                            </div>
                        </div>
                        <span class='tag tag-{cat}'>{cat.title()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"📋 Pre-Brief for {ev['title'][:28]}...",
                             key=f"brief_{ev['id']}", use_container_width=True):
                    st.session_state.prebriefed_event_id = ev['id']
                    st.session_state.page = "Pre-Brief"
                    st.rerun()
        else:
            st.markdown("""
            <div class='ap-card' style='text-align:center; padding:36px;'>
                <div style='font-size:2rem;'>📭</div>
                <div style='color:var(--ap-text-mid); margin-top:8px;'>No activities scheduled for today.</div>
                <div style='color:var(--ap-text-light); font-size:0.85rem;'>
                    Use the AI Generator to create a weekly calendar!
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Needs Attention ──
        if at_risk or declining or low_eng:
            st.markdown("### ⚠️ Needs Your Attention")
            shown = set()
            for r in at_risk + declining:
                if r['id'] in shown:
                    continue
                shown.add(r['id'])
                last     = get_last_activity(r['id'])
                last_str = (f"Last seen: {last['event_date']} — {last['event_title']}"
                            if last else "No activity on record")
                reason   = []
                if r in at_risk:   reason.append("No engagement in 14+ days")
                if r in declining: reason.append("Declining mood trend")
                icon = MOBILITY_ICON.get(r.get('mobility', 'independent'), '⚪')
                st.markdown(f"""
                <div class='ap-card ap-card-terra' style='padding:14px 18px; margin-bottom:8px;'>
                    <div>
                        <strong style='font-size:1rem; color:var(--ap-text);'>{icon} {r['name']}</strong>
                        <span style='color:var(--ap-text-light); font-size:0.8rem;'>
                            &nbsp;· Rm {r.get('room','?')}
                        </span><br>
                        <span style='font-size:0.82rem; color:var(--ap-accent);'>
                            {"  ·  ".join(reason)}
                        </span><br>
                        <span style='font-size:0.78rem; color:var(--ap-text-light);'>{last_str}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            for r, rate in low_eng:
                if r['id'] in shown:
                    continue
                shown.add(r['id'])
                icon = MOBILITY_ICON.get(r.get('mobility', 'independent'), '⚪')
                st.markdown(f"""
                <div class='ap-card ap-card-terra' style='padding:14px 18px; margin-bottom:8px;'>
                    <div>
                        <strong style='font-size:1rem; color:var(--ap-text);'>{icon} {r['name']}</strong>
                        <span style='color:var(--ap-text-light); font-size:0.8rem;'>
                            &nbsp;· Rm {r.get('room','?')}
                        </span><br>
                        <span style='font-size:0.82rem; color:var(--ap-accent);'>
                            Low engagement — {rate}% overall
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Coming Up This Week ──
        st.markdown("### 📆 Coming Up This Week")
        upcoming = [ev for ev in week_events if ev['date'] != today_str]
        if upcoming:
            for ev in upcoming:
                day_label = date.fromisoformat(ev['date']).strftime("%a %b %d")
                cat = ev.get('category', 'social')
                st.markdown(f"""
                <div style='padding:10px 16px; background:var(--ap-surface); border-radius:10px;
                            border:1px solid var(--ap-border); margin-bottom:7px;
                            display:flex; justify-content:space-between; align-items:center;'>
                    <span style='color:var(--ap-text-mid);'>
                        <strong style='color:var(--ap-text);'>{day_label}</strong>
                        &nbsp;· {ev.get('time','TBD')} — {ev['title']}
                    </span>
                    <span class='tag tag-{cat}'>{cat.title()}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No more events this week.")

    # ══════════════════════════════════════
    with col_right:

        # ── Birthdays ──
        st.markdown("### 🎂 Upcoming Birthdays")
        birthday_list = []
        for r in residents:
            bday = r.get('birthday')
            if not bday:
                continue
            try:
                bd        = date.fromisoformat(bday)
                this_year = bd.replace(year=today.year)
                if this_year < today:
                    this_year = this_year.replace(year=today.year + 1)
                days_away = (this_year - today).days
                if days_away <= 30:
                    birthday_list.append((r['name'], this_year, days_away))
            except Exception:
                pass
        birthday_list.sort(key=lambda x: x[2])

        if birthday_list:
            for name, bday_date, days in birthday_list:
                label = "🎉 TODAY!" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
                st.markdown(f"""
                <div style='padding:10px 14px; background:var(--ap-accent-light); border-radius:10px;
                            border:1px solid var(--ap-border); margin-bottom:8px;'>
                    <strong style='color:var(--ap-text);'>{name}</strong><br>
                    <span style='color:var(--ap-text-mid); font-size:0.85rem;'>
                        🎂 {bday_date.strftime("%B %d")} — {label}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='color:var(--ap-text-light); font-size:0.9rem;'>"
                "No birthdays in the next 30 days.</div>",
                unsafe_allow_html=True,
            )

        # ── Suggested activity ──
        st.markdown("### 💡 Suggested for Today")
        if residents and not today_events:
            disability_pool = []
            for r in residents:
                disability_pool.extend((r.get('disabilities') or '').split(','))
            disability_pool = [d.strip() for d in disability_pool if d.strip()]
            most_common = (max(set(disability_pool), key=disability_pool.count)
                           if disability_pool else None)

            from utils.database import get_activities
            suggestions = get_activities()
            if most_common:
                best = [a for a in suggestions
                        if most_common in (a.get('disability_friendly') or '')]
                suggestions = best if best else suggestions

            if suggestions:
                pick = suggestions[0]
                st.markdown(f"""
                <div class='ap-card ap-card-sage'>
                    <div style='font-size:0.75rem; color:var(--ap-primary); font-weight:600;
                                text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;'>
                        Based on your residents' profiles
                    </div>
                    <strong style='font-size:1rem; color:var(--ap-text);'>{pick['title']}</strong><br>
                    <span style='font-size:0.82rem; color:var(--ap-text-light);'>
                        ⏱️ {pick.get('duration_minutes',60)} min &nbsp;·&nbsp;
                        💰 {pick.get('cost_estimate','Free')} &nbsp;·&nbsp;
                        <span class='tag tag-{pick.get("category","social")}'>
                            {(pick.get("category","social")).title()}
                        </span>
                    </span><br>
                    <span style='font-size:0.82rem; color:var(--ap-text-mid); margin-top:6px; display:block;'>
                        {(pick.get('description') or '')[:120]}...
                    </span>
                </div>
                """, unsafe_allow_html=True)
        elif today_events:
            st.markdown("""
            <div class='ap-card ap-card-sage'>
                <div style='color:var(--ap-primary); font-size:0.9rem;'>
                    ✅ You're all set — activities are already scheduled for today!
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Mood snapshot ──
        st.markdown("### 💬 Resident Mood Snapshot")
        st.markdown(
            "<div style='font-size:0.8rem; color:var(--ap-text-light); margin-bottom:10px;'>"
            "Last recorded mood</div>",
            unsafe_allow_html=True,
        )
        shown_any = False
        for r in residents[:10]:
            last = get_last_activity(r['id'])
            if last and last.get('mood_after'):
                mood  = last['mood_after']
                emoji = MOOD_EMOJI.get(mood, "😐")
                icon  = MOBILITY_ICON.get(r.get('mobility', 'independent'), '⚪')
                st.markdown(f"""
                <div style='padding:7px 12px; background:var(--ap-surface); border-radius:8px;
                            border:1px solid var(--ap-border); margin-bottom:5px;
                            display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:0.85rem; color:var(--ap-text);'>{icon} {r['name']}</span>
                    <span style='font-size:1.1rem;' title='Mood after last activity'>{emoji}</span>
                </div>
                """, unsafe_allow_html=True)
                shown_any = True
        if not shown_any:
            st.markdown(
                "<div style='color:var(--ap-text-light); font-size:0.85rem;'>"
                "Rate some activities to see mood data here.</div>",
                unsafe_allow_html=True,
            )

        # ── Quick actions ──
        if is_director():
            st.markdown("### ⚡ Quick Actions")
            for label, page_key in [
                ("👤 Resident Cards",   "Resident Cards"),
                ("👨‍👩‍👧 Family Updates", "Family Updates"),
                ("📊 Reports",          "Reports"),
            ]:
                if st.button(label, key=f"qa_{page_key}", use_container_width=True):
                    st.session_state.page = page_key
                    st.rerun()
