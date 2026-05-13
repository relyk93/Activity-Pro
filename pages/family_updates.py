import csv
import io
import streamlit as st
from utils.database import (get_residents, get_engagements, get_subscription,
                             update_resident_family, mark_family_update_sent)
from utils.email_sender import build_family_update_html, send_email
from utils.auth import require_director
from datetime import date


def _engagement_csv(engs: list) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Activity", "Engaged", "Mood Before", "Mood After", "Rating", "Staff Note"])
    for e in engs:
        w.writerow([
            e["event_date"], e["event_title"], int(e["engaged"]),
            e.get("mood_before", ""), e.get("mood_after", ""),
            e.get("rating", ""), e.get("staff_note", ""),
        ])
    return buf.getvalue()


def show():
    st.markdown("# 👨‍👩‍👧 Family Updates")
    st.markdown(
        "<div style='color:var(--ap-text-light); margin-bottom:20px;'>"
        "Send or download personalized activity updates for each resident's family."
        "</div>",
        unsafe_allow_html=True,
    )

    if not require_director():
        return

    sub = get_subscription()
    facility_name = sub.get("facility_name", "My Facility")
    residents = get_residents()

    if not residents:
        st.info("No residents added yet.")
        return

    # ── SMTP status ──
    try:
        smtp_user = st.secrets.get("SMTP_USER", "")
    except Exception:
        smtp_user = ""

    if not smtp_user:
        with st.expander("⚙️ Email not configured — click to set up SMTP", expanded=False):
            st.markdown("""
**To enable direct email sending, add your SMTP credentials to Streamlit Cloud:**

1. Go to **[share.streamlit.io](https://share.streamlit.io)** → your app → **Settings** → **Secrets**
2. Paste the following block and fill in your details:

```toml
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "you@gmail.com"
SMTP_PASSWORD = "your-app-password"
FROM_EMAIL    = "you@gmail.com"
```

**For Gmail:** Use an [App Password](https://myaccount.google.com/apppasswords) — not your main password.
Go to **Google Account → Security → 2-Step Verification → App Passwords**, generate one for "Mail".

> Until SMTP is configured, use the **Download** buttons below to save updates as HTML files you can open, print, or forward from your own email client.
""")
        st.info("SMTP not set up — use **Download** buttons below to save updates as files.", icon="ℹ️")

    # ── Resident list ──
    for r in residents:
        engs = get_engagements(resident_id=r["id"])
        has_data = len(engs) > 0
        has_email = bool(r.get("family_email"))
        last_sent = r.get("last_update_sent") or "Never"

        status_icon = "✅" if has_email and has_data else "⚠️"
        email_label = f"📧 {r['family_email']}" if has_email else "⚠️ No email on file"

        with st.expander(
            f"{status_icon} **{r['name']}** · Rm {r.get('room','?')} · {email_label} · Last sent: {last_sent}"
        ):
            col_info, col_action = st.columns([2, 1])

            with col_info:
                with st.form(f"family_contact_{r['id']}"):
                    st.markdown("**Family Contact**")
                    family_name = st.text_input(
                        "Contact Name", value=r.get("family_name", "") or "",
                        placeholder="e.g. Susan Thompson (daughter)",
                    )
                    family_email = st.text_input(
                        "Contact Email", value=r.get("family_email", "") or "",
                        placeholder="e.g. susan@example.com",
                    )
                    if st.form_submit_button("Save Contact", use_container_width=True):
                        update_resident_family(r["id"], family_name, family_email)
                        st.success("Saved!")
                        st.rerun()

            with col_action:
                if not has_data:
                    st.markdown(
                        f"<div class='ap-card' style='text-align:center; color:var(--ap-text-light); "
                        f"font-size:0.85rem; padding:12px;'>"
                        f"Rate some activities for {r['name'].split()[0]} first.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    total   = len(engs)
                    engaged = sum(1 for e in engs if e["engaged"])
                    rate    = int(engaged / total * 100)

                    st.markdown(f"""
                    <div class='metric-box' style='margin-bottom:12px;'>
                        <div class='metric-number'>{rate}%</div>
                        <div class='metric-label'>{total} sessions · {engaged} engaged</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("👁️ Preview", key=f"preview_{r['id']}", use_container_width=True):
                        st.session_state[f"show_preview_{r['id']}"] = True

                    uploaded = st.file_uploader(
                        "📸 Attach photos",
                        type=["jpg", "jpeg", "png"],
                        accept_multiple_files=True,
                        key=f"photos_{r['id']}",
                        help="Embedded inline in the email body",
                    )
                    if uploaded:
                        st.caption(f"{len(uploaded)} photo{'s' if len(uploaded) != 1 else ''} attached")

                    # ── Send ──
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    if has_email and smtp_user:
                        if st.button(
                            f"📤 Send to {r.get('family_name') or 'Family'}",
                            key=f"send_{r['id']}", type="primary", use_container_width=True,
                        ):
                            photos = [{"name": f.name, "data": f.read()} for f in (uploaded or [])]
                            html_body = build_family_update_html(r, engs, facility_name, photos=photos)
                            subject   = f"Activity Update — {r['name']} · {date.today().strftime('%B %Y')}"
                            ok, msg   = send_email(r["family_email"], subject, html_body, attachments=photos)
                            if ok:
                                mark_family_update_sent(r["id"])
                                st.success(f"Sent to {r['family_email']}")
                                st.rerun()
                            else:
                                st.error(msg)
                    elif has_email:
                        st.caption("Configure SMTP above to enable direct sending.")
                    st.markdown("</div>", unsafe_allow_html=True)

                    # ── Download ──
                    st.markdown(
                        "<div style='font-size:0.78rem; font-weight:600; color:var(--ap-text-light); "
                        "text-transform:uppercase; letter-spacing:0.06em; margin:10px 0 4px;'>Download</div>",
                        unsafe_allow_html=True,
                    )
                    dl1, dl2 = st.columns(2)
                    fname = r["name"].replace(" ", "_")
                    today = date.today().isoformat()

                    with dl1:
                        html_dl = build_family_update_html(r, engs, facility_name)
                        st.download_button(
                            "📄 HTML",
                            data=html_dl,
                            file_name=f"{fname}_update_{today}.html",
                            mime="text/html",
                            key=f"dl_html_{r['id']}",
                            use_container_width=True,
                            help="Open in browser to print or forward",
                        )
                    with dl2:
                        st.download_button(
                            "📊 CSV",
                            data=_engagement_csv(engs),
                            file_name=f"{fname}_engagement_{today}.csv",
                            mime="text/csv",
                            key=f"dl_csv_{r['id']}",
                            use_container_width=True,
                            help="Full engagement history spreadsheet",
                        )

            # ── Preview pane ──
            if st.session_state.get(f"show_preview_{r['id']}") and has_data:
                st.markdown("---")
                st.markdown("**Email Preview**")
                total   = len(engs)
                engaged = sum(1 for e in engs if e["engaged"])
                rate    = int(engaged / total * 100)
                recent  = engs[:5]

                st.markdown(f"""
                <div style='background:var(--ap-surface-2); border-radius:12px; padding:20px;
                            border:1px solid var(--ap-border); font-size:0.9rem;'>
                    <div style='font-weight:600; margin-bottom:6px;'>
                        Subject: Activity Update — {r['name']} · {date.today().strftime("%B %Y")}
                    </div>
                    <div style='color:var(--ap-text-light); margin-bottom:12px;'>
                        To: {r.get('family_email') or '(no email on file)'}
                        {(' · ' + r.get('family_name','')) if r.get('family_name') else ''}
                    </div>
                    <div style='background:var(--ap-surface); border-radius:8px; padding:16px;
                                border:1px solid var(--ap-border);'>
                        <p>Dear Family of <strong>{r['name']}</strong>,</p>
                        <p style='color:var(--ap-text-light);'>
                            {r['name'].split()[0]} has participated in <strong>{total} activity sessions</strong>
                            with a <strong>{rate}% engagement rate</strong>.
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                for eng in recent:
                    icon = "✅" if eng["engaged"] else "❌"
                    note = f" — {eng['staff_note']}" if eng.get("staff_note") else ""
                    st.markdown(f"- {icon} **{eng['event_date']}** · {eng['event_title']}{note}")

                if st.button("✕ Close Preview", key=f"close_preview_{r['id']}"):
                    st.session_state[f"show_preview_{r['id']}"] = False
                    st.rerun()

    # ── Bulk section ──
    st.markdown("---")
    st.markdown("### 📬 Bulk Actions")

    residents_ready = [
        r for r in residents
        if r.get("family_email") and get_engagements(resident_id=r["id"])
    ]
    st.markdown(
        f"**{len(residents_ready)} residents** have an email on file with engagement data."
    )

    bulk_col1, bulk_col2 = st.columns(2)

    with bulk_col1:
        st.markdown("**Send all via email**")
        if smtp_user and residents_ready:
            if st.button("📤 Send All Family Updates", type="primary", use_container_width=True):
                sent, failed = 0, 0
                for r in residents_ready:
                    engs      = get_engagements(resident_id=r["id"])
                    html_body = build_family_update_html(r, engs, facility_name)
                    subject   = f"Activity Update — {r['name']} · {date.today().strftime('%B %Y')}"
                    ok, _     = send_email(r["family_email"], subject, html_body, attachments=[])
                    if ok:
                        mark_family_update_sent(r["id"])
                        sent += 1
                    else:
                        failed += 1
                st.success(
                    f"Sent {sent} update{'s' if sent != 1 else ''}."
                    + (f" ⚠️ {failed} failed." if failed else "")
                )
                st.rerun()
        elif not smtp_user:
            st.info("Configure SMTP above to enable bulk send.")
        else:
            st.info("Add family emails to residents to enable bulk send.")

    with bulk_col2:
        st.markdown("**Download all engagement data**")
        if residents_ready:
            # Combined CSV: all residents in one file
            combined_buf = io.StringIO()
            w = csv.writer(combined_buf)
            w.writerow(["Resident", "Date", "Activity", "Engaged",
                        "Mood Before", "Mood After", "Rating", "Staff Note"])
            for r in residents_ready:
                for e in get_engagements(resident_id=r["id"]):
                    w.writerow([
                        r["name"], e["event_date"], e["event_title"], int(e["engaged"]),
                        e.get("mood_before", ""), e.get("mood_after", ""),
                        e.get("rating", ""), e.get("staff_note", ""),
                    ])
            st.download_button(
                "📊 Download All Engagement CSV",
                data=combined_buf.getvalue(),
                file_name=f"all_residents_engagement_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
                help="All residents in one spreadsheet",
            )
        else:
            st.info("No residents with engagement data yet.")
