import streamlit as st
from utils.database import get_subscription, update_subscription
from utils.auth import require_director

def show():
    st.markdown("# ⚙️ Settings")

    if not require_director():
        return

    sub = get_subscription()

    tab1, tab2 = st.tabs(["🏥 Facility & Display", "🏥 EHR Integration"])

    with tab1:
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

    with tab2:
        st.markdown("### 🏥 EHR Integration")
        st.markdown("""
        <div class='ap-card ap-card-sky'>
            Connect ActivityPro to your facility's Electronic Health Record system so that
            activity participation data flows directly into resident charts — no double entry.
        </div>
        """, unsafe_allow_html=True)

        ehr_provider = st.selectbox(
            "EHR Provider",
            ["None — Not Connected", "PointClickCare", "MatrixCare"],
            help="Select your facility's EHR platform."
        )

        if ehr_provider == "None — Not Connected":
            st.info("No EHR connected. Select a provider above to configure the integration.")

        elif ehr_provider == "PointClickCare":
            st.markdown("#### PointClickCare Configuration")
            st.markdown("""
            <div class='ap-card ap-card-terra'>
                <strong>Before you begin:</strong> You need a PointClickCare partner/developer account.
                Apply at <em>pointclickcare.com/partners</em> to receive your client credentials.
                Use the <strong>sandbox</strong> environment for testing — no production data is affected.
            </div>
            """, unsafe_allow_html=True)

            with st.form("pcc_form"):
                pcc_client_id     = st.text_input("Client ID",     type="password", placeholder="From PCC developer portal")
                pcc_client_secret = st.text_input("Client Secret", type="password", placeholder="From PCC developer portal")
                pcc_org_uuid      = st.text_input("Org UUID",      placeholder="Your facility's PCC org UUID")
                pcc_sandbox       = st.checkbox("Use sandbox (recommended for testing)", value=True)

                if st.form_submit_button("Test Connection", type="primary"):
                    if not all([pcc_client_id, pcc_client_secret, pcc_org_uuid]):
                        st.error("All three fields are required.")
                    else:
                        try:
                            from utils.ehr_pointclickcare import PointClickCareClient
                            client = PointClickCareClient(pcc_client_id, pcc_client_secret,
                                                          pcc_org_uuid, pcc_sandbox)
                            residents = client.get_residents()
                            st.success(f"✅ Connected! Found {len(residents)} residents in PCC.")
                            st.info("Add these credentials to .streamlit/secrets.toml under [ehr] to persist them.")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")

            st.markdown("""
            **Add to `.streamlit/secrets.toml`:**
            ```toml
            [ehr]
            pcc_client_id     = "your_client_id"
            pcc_client_secret = "your_client_secret"
            pcc_org_uuid      = "your_org_uuid"
            pcc_sandbox       = true
            ```
            """)

        elif ehr_provider == "MatrixCare":
            st.markdown("#### MatrixCare Configuration")
            st.markdown("""
            <div class='ap-card ap-card-terra'>
                <strong>Before you begin:</strong> Contact MatrixCare at <em>matrixcare.com/partners</em>
                to obtain API credentials for your facility. Use the sandbox environment for initial testing.
            </div>
            """, unsafe_allow_html=True)

            with st.form("mc_form"):
                mc_api_key     = st.text_input("API Key",      type="password", placeholder="From MatrixCare partner portal")
                mc_facility_id = st.text_input("Facility ID",  placeholder="Your MatrixCare facility ID")
                mc_sandbox     = st.checkbox("Use sandbox (recommended for testing)", value=True)

                if st.form_submit_button("Test Connection", type="primary"):
                    if not all([mc_api_key, mc_facility_id]):
                        st.error("Both fields are required.")
                    else:
                        try:
                            from utils.ehr_matrixcare import MatrixCareClient
                            client = MatrixCareClient(mc_api_key, mc_facility_id, mc_sandbox)
                            residents = client.get_residents()
                            st.success(f"✅ Connected! Found {len(residents)} residents in MatrixCare.")
                            st.info("Add these credentials to .streamlit/secrets.toml under [ehr] to persist them.")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")

            st.markdown("""
            **Add to `.streamlit/secrets.toml`:**
            ```toml
            [ehr]
            mc_api_key     = "your_api_key"
            mc_facility_id = "your_facility_id"
            mc_sandbox     = true
            ```
            """)
