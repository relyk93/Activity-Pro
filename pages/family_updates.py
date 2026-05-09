import streamlit as st
from utils.database import (get_residents, get_engagements, get_subscription,
                             update_resident_family, mark_family_update_sent)
from utils.email_sender import build_family_update_html, send_email
from utils.auth import require_director
from datetime import date

def show():
    st.markdown("# 👨‍👩‍👧 Family Updates")
    st.markdown(
        "<div style='color:#718096; margin-bottom:20px;'>"
        "Generate and send a personalized activity update email to each resident's family — "
        "one click per resident, no writing required."
        "</div>",
        unsafe_allow_html=True
    )

    if not require_director():
        return

    sub = get_subscription()
    facility_name = sub.get('facility_name', 'My Facility')
    residents = get_residents()

    if not residents:
        st.info("No residents added yet.")
        return

    # ── SMTP warning ──
    try:
        smtp_user = st.secrets.get("SMTP_USER", "")
    except Exception:
        smtp_user = ""
    if not smtp_user:
        st.warning(
            "Email is not configured. Add SMTP settings to `.streamlit/secrets.toml` to enable sending. "
            "You can still preview and copy the update text below."
        )

    # ── Resident list ──
    for r in residents:
        engs = get_engagements(resident_id=r['id'])
        has_data = len(engs) > 0
        has_email = bool(r.get('family_email'))
        last_sent = r.get('last_update_sent') or 'Never'

        # Status indicators
        status_parts = []
        if not has_email:
            status_parts.append("⚠️ No email on file")
        else:
            status_parts.append(f"📧 {r['family_email']}")
        status_parts.append(f"Last sent: {last_sent}")

        with st.expander(
            f"{'✅' if has_email and has_data else '⚠️'} **{r['name']}** "
            f"· Rm {r.get('room','?')} · {' · '.join(status_parts)}"
        ):
            col_info, col_action = st.columns([2, 1])

            with col_info:
                # Family contact form (inline edit)
                with st.form(f"family_contact_{r['id']}"):
                    st.markdown("**Family Contact**")
                    family_name  = st.text_input("Contact Name",  value=r.get('family_name','')  or '',
                                                  placeholder="e.g. Susan Thompson (daughter)")
                    family_email = st.text_input("Contact Email", value=r.get('family_email','') or '',
                                                  placeholder="e.g. susan@example.com")
                    if st.form_submit_button("Save Contact", use_container_width=True):
                        update_resident_family(r['id'], family_name, family_email)
                        st.success("Saved!")
                        st.rerun()

            with col_action:
                if not has_data:
                    st.markdown("""
                    <div style='background:#FAF7F2; border-radius:10px; padding:16px; text-align:center;'>
                        <div style='color:#A0AEC0; font-size:0.85rem;'>
                            Rate some activities for {name} first to populate an update.
                        </div>
                    </div>
                    """.replace("{name}", r['name'].split()[0]), unsafe_allow_html=True)
                else:
                    total = len(engs)
                    engaged = sum(1 for e in engs if e['engaged'])
                    rate = int(engaged / total * 100)

                    st.markdown(f"""
                    <div class='metric-box' style='margin-bottom:10px;'>
                        <div class='metric-number'>{rate}%</div>
                        <div class='metric-label'>{total} sessions · {engaged} engaged</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"👁️ Preview Update", key=f"preview_{r['id']}", use_container_width=True):
                        st.session_state[f"show_preview_{r['id']}"] = True

                    if has_email and smtp_user:
                        if st.button(f"📤 Send to {r.get('family_name') or 'Family'}",
                                     key=f"send_{r['id']}", type="primary", use_container_width=True):
                            html_body = build_family_update_html(r, engs, facility_name)
                            subject   = f"Activity Update — {r['name']} · {date.today().strftime('%B %Y')}"
                            ok, msg   = send_email(r['family_email'], subject, html_body)
                            if ok:
                                mark_family_update_sent(r['id'])
                                st.success(f"✅ Sent to {r['family_email']}")
                                st.rerun()
                            else:
                                st.error(msg)
                    elif has_email and not smtp_user:
                        st.info("Configure SMTP to send.", icon="ℹ️")

            # Preview pane (below both columns, inside expander)
            if st.session_state.get(f"show_preview_{r['id']}") and has_data:
                st.markdown("---")
                st.markdown("**Email Preview**")
                html_body = build_family_update_html(r, engs, facility_name)

                # Plain-text preview
                total   = len(engs)
                engaged = sum(1 for e in engs if e['engaged'])
                rate    = int(engaged / total * 100)
                recent  = engs[:5]

                st.markdown(f"""
                <div style='background:#FAF7F2; border-radius:12px; padding:20px;
                            border:1px solid #E2DDD6; font-size:0.9rem; color:#1A2332;'>
                    <div style='font-size:1rem; font-weight:600; margin-bottom:8px;'>
                        Subject: Activity Update — {r['name']} · {date.today().strftime("%B %Y")}
                    </div>
                    <div style='color:#718096; margin-bottom:12px;'>
                        To: {r.get('family_email') or '(no email on file)'}
                        {(' · ' + r.get('family_name','')) if r.get('family_name') else ''}
                    </div>
                    <div style='background:white; border-radius:8px; padding:16px; border:1px solid #E2DDD6;'>
                        <p>Dear Family of <strong>{r['name']}</strong>,</p>
                        <p style='color:#4A5568;'>
                            We're pleased to share this month's activity update.
                            {r['name'].split()[0]} has participated in <strong>{total} activity sessions</strong>
                            with a <strong>{rate}% engagement rate</strong>.
                        </p>
                        <p style='color:#4A5568;'><strong>Recent sessions:</strong></p>
                        <ul style='color:#4A5568;'>
                """, unsafe_allow_html=True)
                for eng in recent:
                    icon = "✅" if eng['engaged'] else "❌"
                    note = f" — {eng['staff_note']}" if eng.get('staff_note') else ""
                    st.markdown(f"- {icon} **{eng['event_date']}** · {eng['event_title']}{note}")
                st.markdown("""
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("✕ Close Preview", key=f"close_preview_{r['id']}"):
                    st.session_state[f"show_preview_{r['id']}"] = False
                    st.rerun()

    # ── Bulk send button (director convenience) ──
    st.markdown("---")
    st.markdown("### 📬 Send All Updates")
    residents_with_email_and_data = [
        r for r in residents
        if r.get('family_email') and get_engagements(resident_id=r['id'])
    ]
    st.markdown(
        f"**{len(residents_with_email_and_data)} residents** have an email on file with engagement data. "
        "This will send one update email per resident."
    )
    if smtp_user and residents_with_email_and_data:
        if st.button("📤 Send All Family Updates", type="primary"):
            sent, failed = 0, 0
            for r in residents_with_email_and_data:
                engs = get_engagements(resident_id=r['id'])
                html_body = build_family_update_html(r, engs, facility_name)
                subject = f"Activity Update — {r['name']} · {date.today().strftime('%B %Y')}"
                ok, _ = send_email(r['family_email'], subject, html_body)
                if ok:
                    mark_family_update_sent(r['id'])
                    sent += 1
                else:
                    failed += 1
            st.success(f"✅ Sent {sent} update{'s' if sent != 1 else ''}.{' ⚠️ ' + str(failed) + ' failed.' if failed else ''}")
            st.rerun()
    elif not smtp_user:
        st.info("Configure SMTP in secrets.toml to enable bulk send.")
    else:
        st.info("Add family email addresses to residents above to enable bulk send.")
