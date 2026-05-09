import streamlit as st
from utils.auth import login_staff

def show():
    st.markdown("""
    <div style='max-width:420px; margin:60px auto 0 auto;'>
        <div style='text-align:center; margin-bottom:32px;'>
            <div style='font-family: Playfair Display, serif; font-size:2.4rem; font-weight:700;
                        color: var(--ap-text);'>🌸 ActivityPro</div>
            <div style='font-size:0.82rem; color: var(--ap-text-light); margin-top:6px;
                        letter-spacing:0.1em; text-transform:uppercase;'>Senior Care Calendar</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("""
        <div class='ap-card' style='padding:32px; text-align:center;'>
            <h3 style='margin-bottom:6px;'>Welcome back</h3>
            <p style='color: var(--ap-text-light); font-size:0.85rem; margin-bottom:0;'>
                Sign in to access your facility dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif login_staff(username.strip(), password):
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        st.markdown("""
        <div style='background: var(--ap-primary-light); border:1px solid var(--ap-primary);
                    border-radius:12px; padding:16px; margin-top:16px;'>
            <div style='font-size:0.78rem; font-weight:700; color: var(--ap-primary);
                        letter-spacing:0.06em; text-transform:uppercase; margin-bottom:10px;'>
                ✦ Live Demo Access
            </div>
            <div style='font-size:0.85rem; color: var(--ap-text); line-height:1.9;'>
                <strong>Director view</strong><br>
                <code style='background:rgba(15,118,110,0.1); padding:2px 8px; border-radius:6px;
                             font-size:0.82rem;'>director</code> &nbsp;/&nbsp;
                <code style='background:rgba(15,118,110,0.1); padding:2px 8px; border-radius:6px;
                             font-size:0.82rem;'>ActivityPro2024!</code><br><br>
                <strong>Floor staff view</strong><br>
                <code style='background:rgba(15,118,110,0.1); padding:2px 8px; border-radius:6px;
                             font-size:0.82rem;'>staff1</code> &nbsp;/&nbsp;
                <code style='background:rgba(15,118,110,0.1); padding:2px 8px; border-radius:6px;
                             font-size:0.82rem;'>Staff2024!</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
