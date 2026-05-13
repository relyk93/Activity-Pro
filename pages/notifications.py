import streamlit as st
from utils.database import get_residents, get_events, get_engagements, get_subscription
from utils.email_sender import send_email, build_staff_reminder_html
from utils.auth import require_director
from datetime import date, timedelta


def show():
    st.markdown("# 🔔 Notifications")
    st.markdown(
        "<div style='color:var(--ap-text-light); margin-bottom:20px;'>"
        "Staff daily schedule reminders, low-engagement alerts, and upcoming birthday flags."
        "</div>",
        unsafe_allow_html=True,
    )

    if not require_director():
        return

    try:
        smtp_user      = st.secrets.get("SMTP_USER", "")
        email_configured = bool(smtp_user)
    except Exception:
        email_configured = False

    sub           = get_subscription()
    facility_name = sub.get("facility_name", "My Facility")
    residents     = get_residents()
    today         = date.today()

    # ── SMTP banner ──
    if not email_configured:
        with st.expander("⚙️ Email not configured — staff reminders won't send", expanded=False):
            st.markdown("""
Go to **[share.streamlit.io](https://share.streamlit.io)** → your app → **Settings → Secrets** and add:

```toml
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "you@gmail.com"
SMTP_PASSWORD = "your-app-password"
FROM_EMAIL    = "you@gmail.com"
```
For Gmail use an [App Password](https://myaccount.google.com/apppasswords), not your main password.
""")

    tab1, tab2, tab3 = st.tabs(["⚠️ Alerts", "☀️ Staff Reminder", "🎂 Birthdays"])

    # ─── Tab 1: Alerts ───
    with tab1:
        st.markdown("### Resident Alerts")

        if not residents:
            st.info("Add residents to see alerts.")
        else:
            from utils.database import get_at_risk_residents, get_declining_mood_residents, get_last_activity
            at_risk   = get_at_risk_residents(days_threshold=14)
            declining = get_declining_mood_residents()

            # Low engagement list
            low_eng = []
            for r in residents:
                engs = get_engagements(resident_id=r['id'])
                if engs:
                    rate = int(sum(1 for e in engs if e['engaged']) / len(engs) * 100)
                    if rate < 40:
                        low_eng.append((r, rate))

            alert_count = len(at_risk) + len(declining) + len(low_eng)
            if alert_count == 0:
                st.success("✅ No alerts — all residents are engaged and moods are stable.")
            else:
                st.markdown(f"**{alert_count} alert{'s' if alert_count != 1 else ''} need attention**")

            if at_risk:
                st.markdown("#### No Engagement in 14+ Days")
                for r in at_risk:
                    last = get_last_activity(r['id'])
                    last_str = (
                        f"Last: {last['event_title']} on {last['event_date']}"
                        if last else "No activity on record"
                    )
                    st.markdown(f"""
                    <div class='ap-card ap-card-terra' style='padding:12px 16px; margin-bottom:8px;'>
                        <strong style='color:var(--ap-text);'>⚠️ {r['name']}</strong>
                        <span style='color:var(--ap-text-light); font-size:0.82rem;'>
                            &nbsp;· Rm {r.get('room','?')}
                        </span><br>
                        <span style='font-size:0.82rem; color:var(--ap-text-mid);'>{last_str}</span>
                    </div>
                    """, unsafe_allow_html=True)

            if declining:
                st.markdown("#### Declining Mood Trend")
                for r in declining:
                    st.markdown(f"""
                    <div class='ap-card ap-card-terra' style='padding:12px 16px; margin-bottom:8px;'>
                        <strong style='color:var(--ap-text);'>📉 {r['name']}</strong>
                        <span style='color:var(--ap-text-light); font-size:0.82rem;'>
                            &nbsp;· Rm {r.get('room','?')}
                        </span><br>
                        <span style='font-size:0.82rem; color:var(--ap-text-mid);'>
                            Mood scores trending downward — consider a 1-on-1 check-in.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

            if low_eng:
                st.markdown("#### Low Engagement (below 40%)")
                for r, rate in low_eng:
                    st.markdown(f"""
                    <div class='ap-card ap-card-terra' style='padding:12px 16px; margin-bottom:8px;'>
                        <strong style='color:var(--ap-text);'>📊 {r['name']}</strong>
                        <span style='color:var(--ap-text-light); font-size:0.82rem;'>
                            &nbsp;· Rm {r.get('room','?')}
                        </span><br>
                        <span style='font-size:0.82rem; color:var(--ap-accent);'>
                            {rate}% engagement — consider personalised AI activities.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    # ─── Tab 2: Staff Reminder ───
    with tab2:
        st.markdown("### Daily Staff Schedule Reminder")
        st.markdown(
            "<div style='color:var(--ap-text-light); margin-bottom:16px;'>"
            "Send today's activity schedule to your team by email — great for morning handoffs."
            "</div>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            staff_email    = st.text_input("Staff email address",
                                           placeholder="staff@facility.com")
            reminder_date  = st.date_input("Schedule date", value=today)
        with col2:
            date_events = get_events(date_from=str(reminder_date), date_to=str(reminder_date))
            st.markdown(f"""
            <div class='metric-box' style='margin-top:20px;'>
                <div class='metric-number'>{len(date_events)}</div>
                <div class='metric-label'>Activities on {reminder_date.strftime('%b %d')}</div>
            </div>
            """, unsafe_allow_html=True)

        if date_events:
            with st.expander("👁️ Preview email", expanded=False):
                html_preview = build_staff_reminder_html(date_events, facility_name)
                st.components.v1.html(html_preview, height=420, scrolling=True)

            if st.button("📤 Send Staff Reminder", type="primary",
                         disabled=not staff_email, use_container_width=True):
                if email_configured and staff_email:
                    html_body = build_staff_reminder_html(date_events, facility_name)
                    subject   = f"Today's Activity Schedule — {reminder_date.strftime('%A, %B %d')}"
                    ok, msg   = send_email(staff_email, subject, html_body)
                    if ok:
                        st.success(f"Sent to {staff_email}")
                    else:
                        st.error(msg)
                else:
                    st.warning("Enter a staff email and configure SMTP to send.")
        else:
            st.info(f"No activities on {reminder_date.strftime('%B %d')} — add some to the calendar first.")

    # ─── Tab 3: Birthdays ───
    with tab3:
        st.markdown("### Upcoming Birthdays — Next 30 Days")

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
                    birthday_list.append((r, this_year, days_away))
            except Exception:
                pass
        birthday_list.sort(key=lambda x: x[2])

        if not birthday_list:
            st.info("No birthdays in the next 30 days.")
        else:
            for r, bday_date, days in birthday_list:
                label = "🎉 TODAY!" if days == 0 else (
                    "Tomorrow!" if days == 1 else f"in {days} days"
                )
                urgency = "ap-card-terra" if days <= 3 else "ap-card-sage"
                st.markdown(f"""
                <div class='ap-card {urgency}' style='padding:14px 18px; margin-bottom:8px;'>
                    <strong style='color:var(--ap-text); font-size:1rem;'>
                        🎂 {r['name']}
                    </strong>
                    <span style='color:var(--ap-text-light); font-size:0.82rem;'>
                        &nbsp;· Rm {r.get('room','?')}
                    </span><br>
                    <span style='font-size:0.88rem; color:var(--ap-text-mid);'>
                        {bday_date.strftime('%B %d')} — <strong>{label}</strong>
                    </span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption("Add or update birthday dates on the Residents page.")
