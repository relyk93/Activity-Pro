import streamlit as st
from utils.database import get_subscription, update_subscription

def show():
    st.markdown("# ⚙️ Settings")

    sub = get_subscription()

    with st.form("settings_form"):
        st.markdown("### 🏥 Facility Information")
        facility_name = st.text_input("Facility Name", value=sub.get('facility_name', 'My Facility'))
        admin_email = st.text_input("Admin Email", value=sub.get('admin_email', ''))

        st.markdown("---")
        st.markdown("### 🌐 Display Preferences")
        language = st.selectbox("Language", ["English", "Spanish", "French", "Portuguese", "Mandarin", "Japanese"])
        timezone = st.selectbox("Timezone", ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific", "Europe/London", "Europe/Paris", "Asia/Tokyo"])
        date_format = st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])

        st.markdown("---")
        st.markdown("### 🔔 Notifications")
        birthday_notif = st.checkbox("Remind me of upcoming birthdays (7 days ahead)", value=True)
        low_engagement = st.checkbox("Alert when resident engagement drops below 40%", value=True)

        submitted = st.form_submit_button("Save Settings", type="primary")
        if submitted:
            update_subscription(sub['tier'], facility_name=facility_name)
            st.session_state.facility_name = facility_name
            st.success("✅ Settings saved!")
