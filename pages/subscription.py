import streamlit as st
from utils.database import get_subscription, update_subscription, activate_stripe_subscription
from utils.stripe_utils import (
    stripe_configured, create_checkout_session,
    verify_checkout_session, create_portal_session
)

def _app_url() -> str:
    try:
        return st.secrets.get("APP_URL", "http://localhost:8501")
    except Exception:
        return "http://localhost:8501"

def show():
    sub = get_subscription()
    current_tier = sub.get('tier', 'free')
    stripe_customer_id = sub.get('stripe_customer_id', '')

    # ── Handle Stripe redirect back to app ──
    params = st.query_params
    if params.get("stripe_success") and params.get("session_id"):
        session_id = params["session_id"]
        with st.spinner("Confirming your payment..."):
            info = verify_checkout_session(session_id)
        if info:
            activate_stripe_subscription(info["stripe_customer_id"], info["stripe_subscription_id"])
            st.session_state.subscription = "professional"
            st.query_params.clear()
            st.success("Payment confirmed! Your Professional plan is now active.")
            st.rerun()
        else:
            st.warning("Could not verify payment — please contact support.")
            st.query_params.clear()

    if params.get("stripe_cancelled"):
        st.info("Checkout was cancelled — no charge was made.")
        st.query_params.clear()

    # ── Page header ──
    st.markdown("# 💳 Subscription")

    tier_labels = {
        "free":         ("Demo", "var(--ap-text-light)"),
        "professional": ("Professional", "var(--ap-primary)"),
        "pro":          ("Professional", "var(--ap-primary)"),
        "enterprise":   ("Enterprise", "var(--ap-accent)"),
    }
    label, color = tier_labels.get(current_tier, ("Demo", "var(--ap-text-light)"))
    st.markdown(f"""
    <div class='ap-card' style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
        <div>
            <div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em;
                        color:var(--ap-text-light); margin-bottom:4px;'>Current Plan</div>
            <div style='font-size:1.5rem; font-weight:700; color:{color};'>{label}</div>
        </div>
        <div style='margin-left:auto; font-size:0.85rem; color:var(--ap-text-light);'>
            {sub.get('facility_name','My Facility')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Plan cards ──
    col1, col2, col3 = st.columns(3)

    # DEMO
    with col1:
        is_current = current_tier in ("free",)
        st.markdown(f"""
        <div class='ap-card' style='border:{"2px solid var(--ap-primary)" if is_current else "1px solid var(--ap-border)"};
             text-align:center; height:100%;'>
            <div style='font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
                        color:var(--ap-text-light); margin-bottom:8px;'>Demo</div>
            <div style='font-size:2.4rem; font-weight:700; color:var(--ap-text); margin-bottom:4px;'>Free</div>
            <div style='font-size:0.82rem; color:var(--ap-text-light); margin-bottom:20px;'>No time limit</div>
            <hr style='border-color:var(--ap-border); margin-bottom:16px;'>
            <div style='font-size:0.85rem; color:var(--ap-text-mid); text-align:left; line-height:2;'>
                ✓ Up to 15 residents<br>
                ✓ Full activity calendar<br>
                ✓ 12-activity library<br>
                ✓ Engagement tracking<br>
                ✓ Resident Quick Cards<br>
                ✓ Session Pre-Brief<br>
                ✓ Staff logins & roles<br>
                — AI generation<br>
                — Analytics & reports<br>
                — Family email updates
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_current:
            st.success("Current plan", icon="✓")
        else:
            if st.button("Switch to Demo", use_container_width=True, key="btn_free"):
                update_subscription("free")
                st.session_state.subscription = "free"
                st.rerun()

    # PROFESSIONAL
    with col2:
        is_current = current_tier in ("pro", "professional")
        stripe_ready = stripe_configured()
        st.markdown(f"""
        <div class='ap-card' style='border:{"2px solid var(--ap-primary)" if is_current else "2px solid var(--ap-primary)"};
             box-shadow: 0 8px 32px rgba(15,118,110,0.15); text-align:center; height:100%;'>
            <div style='font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
                        color:var(--ap-primary); margin-bottom:8px;'>Professional</div>
            <div style='font-size:2.4rem; font-weight:700; color:var(--ap-text); margin-bottom:4px;'>$49</div>
            <div style='font-size:0.82rem; color:var(--ap-text-light); margin-bottom:20px;'>per month · billed monthly</div>
            <hr style='border-color:var(--ap-border); margin-bottom:16px;'>
            <div style='font-size:0.85rem; color:var(--ap-text-mid); text-align:left; line-height:2;'>
                ✓ <strong>Unlimited residents</strong><br>
                ✓ Everything in Demo<br>
                ✓ <strong>AI activity generation</strong><br>
                ✓ Mood tracking before & after<br>
                ✓ Trend charts & analytics<br>
                ✓ Clinical PDF reports<br>
                ✓ Family email updates<br>
                ✓ Photo documentation<br>
                ✓ Smart daily briefing<br>
                ✓ 19 disability types
            </div>
        </div>
        """, unsafe_allow_html=True)

        if is_current:
            st.success("Current plan", icon="✓")
            if stripe_customer_id:
                if st.button("Manage Billing →", use_container_width=True, key="btn_portal"):
                    url = create_portal_session(stripe_customer_id, _app_url())
                    if url:
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)
                    else:
                        st.error("Could not open billing portal.")
        else:
            if stripe_ready:
                if st.button("Upgrade to Professional →", type="primary", use_container_width=True, key="btn_pro"):
                    url = create_checkout_session(
                        sub.get("facility_name", "My Facility"),
                        sub.get("admin_email", ""),
                        _app_url()
                    )
                    if url:
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)
            else:
                st.button("Upgrade to Professional →", type="primary",
                          use_container_width=True, key="btn_pro_disabled", disabled=True)
                st.caption("Add STRIPE_SECRET_KEY + STRIPE_PRICE_ID to secrets.toml to enable payments.")

    # ENTERPRISE
    with col3:
        is_current = current_tier == "enterprise"
        st.markdown(f"""
        <div class='ap-card' style='border:{"2px solid var(--ap-accent)" if is_current else "1px solid var(--ap-border)"};
             text-align:center; height:100%;'>
            <div style='font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase;
                        color:var(--ap-accent); margin-bottom:8px;'>Enterprise</div>
            <div style='font-size:2.4rem; font-weight:700; color:var(--ap-text); margin-bottom:4px;'>Custom</div>
            <div style='font-size:0.82rem; color:var(--ap-text-light); margin-bottom:20px;'>pricing for your organization</div>
            <hr style='border-color:var(--ap-border); margin-bottom:16px;'>
            <div style='font-size:0.85rem; color:var(--ap-text-mid); text-align:left; line-height:2;'>
                ✓ Everything in Professional<br>
                ✓ <strong>Multi-facility management</strong><br>
                ✓ EHR integration (PCC, MatrixCare)<br>
                ✓ HIPAA-compliant cloud backup<br>
                ✓ Facility comparison reports<br>
                ✓ White-label & custom branding<br>
                ✓ API access<br>
                ✓ Dedicated account manager<br>
                ✓ Custom onboarding & training<br>
                ✓ Revenue share / royalty options
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_current:
            st.success("Current plan", icon="✓")
        else:
            st.link_button(
                "Contact Us →",
                "mailto:kyl3rking@gmail.com?subject=ActivityPro%20Enterprise%20Inquiry",
                use_container_width=True,
            )

    # ── Footer ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; font-size:0.82rem; color:var(--ap-text-light);'>
        🔒 Secure billing powered by Stripe &nbsp;·&nbsp; Cancel anytime &nbsp;·&nbsp;
        Questions? <a href="mailto:kyl3rking@gmail.com" style="color:var(--ap-primary);">kyl3rking@gmail.com</a>
    </div>
    """, unsafe_allow_html=True)
