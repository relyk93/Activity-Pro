import streamlit as st
from utils.auth import login_staff

def show():
    st.markdown("""
    <div style='max-width:420px; margin:60px auto 0 auto;'>
        <div style='text-align:center; margin-bottom:32px;'>
            <div style='font-family: Playfair Display, serif; font-size:2.2rem; font-weight:700; color:#2C3E50;'>🌸 ActivityPro</div>
            <div style='font-size:0.85rem; color:#718096; margin-top:6px; letter-spacing:0.08em; text-transform:uppercase;'>Senior Care Calendar</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("""
        <div class='ap-card' style='padding:32px;'>
            <h3 style='text-align:center; margin-bottom:8px;'>Staff Login</h3>
            <p style='text-align:center; color:#718096; font-size:0.85rem; margin-bottom:24px;'>Sign in to access your facility dashboard</p>
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
                    st.error("Invalid username or password.")

        st.markdown("""
        <div style='background:#F0F7F0; border:1px solid #A8C5AA; border-radius:10px; padding:14px; margin-top:16px;'>
            <div style='font-size:0.8rem; font-weight:600; color:#4A6B4C; margin-bottom:6px;'>Demo Credentials</div>
            <div style='font-size:0.8rem; color:#4A5568;'>
                <strong>Director:</strong> director / ActivityPro2024!<br>
                <strong>Staff:</strong> staff1 / Staff2024!
            </div>
        </div>
        """, unsafe_allow_html=True)
