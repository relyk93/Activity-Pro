import streamlit as st
from utils.database import get_subscription, update_subscription

def show():
    st.markdown("# 💳 Subscription")
    st.markdown("<div style='color:#718096; margin-bottom:24px;'>Choose the plan that's right for your facility.</div>", unsafe_allow_html=True)

    sub = get_subscription()
    current_tier = sub.get('tier', 'free')

    # Pricing cards
    col1, col2, col3 = st.columns(3)

    with col1:
        is_current = current_tier == "free"
        st.markdown(f"""
        <div class='ap-card' style='border: {"2px solid #7C9A7E" if is_current else "1px solid #E2DDD6"}; text-align:center;'>
            <div style='font-size:1.5rem; margin-bottom:8px;'>🌱</div>
            <h3 style='margin:0;'>Free</h3>
            <div style='font-size:2rem; font-weight:700; color:#1A2332; margin:12px 0;'>$0<span style='font-size:1rem; font-weight:400; color:#718096;'>/mo</span></div>
            <div style='font-size:0.85rem; color:#4A5568; text-align:left; margin-bottom:20px;'>
                ✅ Up to 15 residents<br>
                ✅ Basic calendar<br>
                ✅ Activity library<br>
                ✅ Activity directions<br>
                ✅ Basic engagement rating<br>
                ❌ AI calendar generation<br>
                ❌ Mood tracking<br>
                ❌ Reports & analytics<br>
                ❌ Disability personalization
            </div>
            {'<div style="background:#7C9A7E; color:white; padding:8px; border-radius:8px; font-weight:600;">Current Plan</div>' if is_current else ''}
        </div>
        """, unsafe_allow_html=True)
        if not is_current:
            if st.button("Switch to Free", use_container_width=True, key="btn_free"):
                update_subscription("free")
                st.session_state.subscription = "free"
                st.success("Switched to Free tier.")
                st.rerun()

    with col2:
        is_current = current_tier == "pro"
        st.markdown(f"""
        <div class='ap-card' style='border: {"2px solid #D4A843" if is_current else "1px solid #E2DDD6"}; text-align:center; background: {"linear-gradient(135deg,#FFFBE8,#FFFFF5)" if is_current else "#FFFDF9"};'>
            <div style='font-size:1.5rem; margin-bottom:8px;'>⭐</div>
            <h3 style='margin:0;'>Pro</h3>
            <div style='font-size:2rem; font-weight:700; color:#1A2332; margin:12px 0;'>$29<span style='font-size:1rem; font-weight:400; color:#718096;'>/mo</span></div>
            <div style='font-size:0.85rem; color:#4A5568; text-align:left; margin-bottom:20px;'>
                ✅ Unlimited residents<br>
                ✅ Everything in Free<br>
                ✅ <strong>AI calendar generation</strong><br>
                ✅ Mood tracking (before/after)<br>
                ✅ Full reports & analytics<br>
                ✅ Disability-aware AI activities<br>
                ✅ Personalized resident activities<br>
                ✅ Birthday awareness<br>
                ✅ Care plan summaries<br>
                ✅ Activity effectiveness ranking<br>
                ❌ Multi-facility management
            </div>
            {'<div style="background:#D4A843; color:#5A3A00; padding:8px; border-radius:8px; font-weight:600;">Current Plan ✓</div>' if is_current else ''}
        </div>
        """, unsafe_allow_html=True)
        if not is_current:
            if st.button("⭐ Upgrade to Pro — $29/mo", type="primary", use_container_width=True, key="btn_pro"):
                update_subscription("pro")
                st.session_state.subscription = "pro"
                st.success("✅ Upgraded to Pro! All features unlocked.")
                st.rerun()

    with col3:
        is_current = current_tier == "enterprise"
        st.markdown(f"""
        <div class='ap-card' style='border: {"2px solid #7C9A7E" if is_current else "1px solid #E2DDD6"}; text-align:center;'>
            <div style='font-size:1.5rem; margin-bottom:8px;'>🏢</div>
            <h3 style='margin:0;'>Enterprise</h3>
            <div style='font-size:2rem; font-weight:700; color:#1A2332; margin:12px 0;'>$79<span style='font-size:1rem; font-weight:400; color:#718096;'>/mo</span></div>
            <div style='font-size:0.85rem; color:#4A5568; text-align:left; margin-bottom:20px;'>
                ✅ Everything in Pro<br>
                ✅ Multi-facility management<br>
                ✅ Facility comparison reports<br>
                ✅ Multilingual support<br>
                ✅ API access<br>
                ✅ Priority support<br>
                ✅ Onboarding & training<br>
                ✅ Custom branding<br>
                ✅ HIPAA-compliant cloud backup<br>
                ✅ Dedicated account manager
            </div>
            {'<div style="background:#7C9A7E; color:white; padding:8px; border-radius:8px; font-weight:600;">Current Plan ✓</div>' if is_current else ''}
        </div>
        """, unsafe_allow_html=True)
        if not is_current:
            if st.button("🏢 Upgrade to Enterprise — $79/mo", use_container_width=True, key="btn_enterprise"):
                update_subscription("enterprise")
                st.session_state.subscription = "enterprise"
                st.success("✅ Upgraded to Enterprise!")
                st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; color:#A0AEC0; font-size:0.85rem;'>
        🔒 Secure billing powered by Stripe &nbsp;|&nbsp; Cancel anytime &nbsp;|&nbsp; 14-day free trial on all paid plans<br>
        📧 Questions? Contact us at <strong>support@activitypro.app</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🌍 Used Worldwide")
    st.markdown("""
    <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-top:16px;'>
        <div class='ap-card' style='text-align:center;'>
            <div style='font-size:2rem; font-weight:700; color:#7C9A7E;'>2,400+</div>
            <div style='color:#718096; font-size:0.85rem;'>Activity Directors</div>
        </div>
        <div class='ap-card' style='text-align:center;'>
            <div style='font-size:2rem; font-weight:700; color:#7C9A7E;'>48</div>
            <div style='color:#718096; font-size:0.85rem;'>Countries</div>
        </div>
        <div class='ap-card' style='text-align:center;'>
            <div style='font-size:2rem; font-weight:700; color:#7C9A7E;'>120K+</div>
            <div style='color:#718096; font-size:0.85rem;'>Residents Served</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
