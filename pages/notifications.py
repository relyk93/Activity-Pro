import streamlit as st
from utils.database import get_residents, get_events, get_engagements, get_subscription
from utils.email_sender import send_email, build_family_update_html, build_staff_reminder_html
from datetime import date, timedelta

def show():
    st.markdown("# 🔔 Notifications & Email")
    st.markdown("<div style='color:#718096; margin-bottom:20px;'>Send family updates, staff reminders, and activity schedules by email.</div>", unsafe_allow_html=True)

    # Check email config
    try:
        import streamlit as st
        smtp_user = st.secrets.get("SMTP_USER", "")
        email_configured = bool(smtp_user)
    except Exception:
        email_configured = False

    if not email_configured:
        st.markdown("""
        <div class='ap-card ap-card-terra'>
            <strong>📧 Email Not Configured Yet</strong><br>
            <div style='color:#4A5568; margin-top:8px; font-size:0.9rem;'>
                To enable email notifications, add your SMTP settings to
                <code>.streamlit/secrets.toml</code>. See the template at
                <code>.streamlit/secrets.toml.template</code> for instructions.<br><br>
                <strong>Quick setup with Gmail:</strong><br>
                1. Enable 2-factor authentication on your Gmail<br>
                2. Go to Google Account → Security → App Passwords<br>
                3. Generate an app password and paste it in secrets.toml<br><br>
                You can still preview all emails below — they'll show exactly what families would receive.
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📧 Family Update Emails", "☀️ Staff Daily Reminder", "⚙️ Email Settings"])

    # ─── Tab 1: Family Updates ───
    with tab1:
        st.markdown("### Send Family Activity Updates")
        st.markdown("Families love knowing how their loved one is doing. These emails include engagement stats, recent activity logs, and staff observations.")

        residents = get_residents()
        if not residents:
            st.info("Add residents first.")
            return

        # Resident selector
        col1, col2 = st.columns([2,1])
        with col1:
            resident_names = [r['name'] for r in residents]
            selected_names = st.multiselect("Select residents to email families for", resident_names, default=[resident_names[0]] if resident_names else [])
        with col2:
            send_mode = st.radio("Send mode", ["Preview only", "Send email"], index=0)

        if not selected_names:
            st.info("Select at least one resident.")
        else:
            for name in selected_names:
                resident = next(r for r in residents if r['name'] == name)
                engs = get_engagements(resident_id=resident['id'])
                sub = get_subscription()
                facility_name = sub.get('facility_name', 'My Facility')

                with st.expander(f"📧 Email preview for **{name}**"):
                    if not engs:
                        st.warning(f"No engagement records for {name} yet. Rate some activities first.")
                        continue

                    total = len(engs)
                    engaged = sum(1 for e in engs if e['engaged'])
                    rate = int(engaged/total*100) if total else 0

                    col_a, col_b = st.columns([3,1])
                    with col_a:
                        family_email = st.text_input(f"Family email for {name}", placeholder="family@email.com", key=f"email_{resident['id']}")
                        subject = st.text_input("Subject line",
                            value=f"Monthly Activity Update for {name} — {date.today().strftime('%B %Y')}",
                            key=f"subject_{resident['id']}")
                    with col_b:
                        st.markdown(f"""
                        <div class='metric-box' style='margin-top:20px;'>
                            <div class='metric-number' style='font-size:1.5rem;'>{rate}%</div>
                            <div class='metric-label'>Engagement</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Preview email
                    html_preview = build_family_update_html(resident, engs, facility_name)
                    st.markdown("**Email Preview:**")
                    st.components.v1.html(html_preview, height=500, scrolling=True)

                    if send_mode == "Send email":
                        if st.button(f"📤 Send to {family_email or '[enter email above]'}", key=f"send_{resident['id']}",
                                     type="primary", disabled=not family_email):
                            if email_configured:
                                success, msg = send_email(family_email, subject, html_preview)
                                if success:
                                    st.success(f"✅ {msg}")
                                else:
                                    st.error(f"❌ {msg}")
                            else:
                                st.warning("Configure SMTP in secrets.toml to send real emails.")

        # Bulk send button
        if send_mode == "Send email" and len(selected_names) > 1:
            st.markdown("---")
            if st.button("📤 Send All Family Emails at Once", type="primary", use_container_width=True):
                st.info("Individual send buttons above — bulk send coming in Phase 3!")

    # ─── Tab 2: Staff Reminders ───
    with tab2:
        st.markdown("### Daily Staff Activity Reminder")
        st.markdown("Send today's schedule to your activity staff every morning — great for shift handoffs.")

        today_str = str(date.today())
        today_events = get_events(date_from=today_str, date_to=today_str)
        sub = get_subscription()
        facility_name = sub.get('facility_name', 'My Facility')

        col1, col2 = st.columns(2)
        with col1:
            staff_email = st.text_input("Staff email address", placeholder="staff@facility.com")
            reminder_date = st.date_input("Send schedule for", value=date.today())

        with col2:
            date_events = get_events(date_from=str(reminder_date), date_to=str(reminder_date))
            st.markdown(f"""
            <div class='metric-box' style='margin-top:20px;'>
                <div class='metric-number'>{len(date_events)}</div>
                <div class='metric-label'>Activities on {reminder_date.strftime('%b %d')}</div>
            </div>
            """, unsafe_allow_html=True)

        if date_events:
            html_preview = build_staff_reminder_html(date_events, facility_name)
            st.markdown("**Email Preview:**")
            st.components.v1.html(html_preview, height=400, scrolling=True)

            if st.button("📤 Send Staff Reminder", type="primary", disabled=not staff_email):
                if email_configured and staff_email:
                    subject = f"Today's Activity Schedule — {reminder_date.strftime('%A, %B %d')}"
                    success, msg = send_email(staff_email, subject, html_preview)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Add staff email above and configure SMTP in secrets.toml.")
        else:
            st.info(f"No activities scheduled for {reminder_date.strftime('%B %d')}. Add activities to the calendar first.")

        # Low engagement alert preview
        st.markdown("---")
        st.markdown("### ⚠️ Low Engagement Alerts")
        st.markdown("Automatically flags residents whose engagement has dropped below 40% this month.")

        residents = get_residents()
        low_eng = []
        for r in residents:
            engs = get_engagements(resident_id=r['id'])
            if engs:
                rate = int(sum(1 for e in engs if e['engaged']) / len(engs) * 100)
                if rate < 40:
                    low_eng.append((r, rate))

        if low_eng:
            st.markdown(f"**{len(low_eng)} residents need attention:**")
            for r, rate in low_eng:
                st.markdown(f"""
                <div class='ap-card ap-card-terra'>
                    ⚠️ <strong>{r['name']}</strong> — Room {r.get('room','?')} · Only <strong>{rate}% engagement</strong><br>
                    <span style='color:#718096; font-size:0.85rem;'>Consider personalized AI activities or one-on-one engagement.</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ All residents are above the 40% engagement threshold!")

    # ─── Tab 3: Email Settings ───
    with tab3:
        st.markdown("### Email Configuration Guide")
        st.markdown("""
        <div class='ap-card'>
        <h4 style='margin-top:0;'>📧 Setting Up Email (Gmail — Recommended)</h4>

        <strong>Step 1:</strong> Enable 2-Factor Authentication on your Gmail account.<br><br>
        <strong>Step 2:</strong> Go to <code>myaccount.google.com → Security → App Passwords</code><br><br>
        <strong>Step 3:</strong> Create an App Password for "Mail"<br><br>
        <strong>Step 4:</strong> Edit <code>.streamlit/secrets.toml</code> in your project folder:<br>
        <pre style='background:#F5F9F5; padding:12px; border-radius:8px; font-size:0.85rem;'>
ANTHROPIC_API_KEY = "sk-ant-your-key"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "yourname@gmail.com"
SMTP_PASSWORD = "your-16-char-app-password"
FROM_EMAIL = "ActivityPro &lt;yourname@gmail.com&gt;"
        </pre>
        <strong>Step 5:</strong> Restart Streamlit — emails will now work!<br><br>
        <div style='background:#FFF8E8; border:1px solid #F0D090; border-radius:8px; padding:12px; margin-top:8px;'>
            ⚠️ <strong>Never commit secrets.toml to GitHub.</strong> It's already in .gitignore to protect your credentials.
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='ap-card ap-card-sage' style='margin-top:16px;'>
        <h4 style='margin-top:0;'>🌐 When Deployed to Streamlit Cloud</h4>
        Instead of a secrets.toml file, paste your secrets into the Streamlit Cloud dashboard:<br><br>
        App Settings → Secrets → paste the same key=value pairs from secrets.toml.<br><br>
        See <code>docs/DEPLOYMENT.md</code> for the full deployment guide.
        </div>
        """, unsafe_allow_html=True)
