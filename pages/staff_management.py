import streamlit as st
from utils.auth import require_director, get_current_staff
from utils.database import get_all_staff, create_staff, update_staff, deactivate_staff

def show():
    st.markdown("# 👤 Staff Management")
    st.markdown("<div style='color:#718096; margin-bottom:20px;'>Manage staff accounts and access levels for your facility.</div>", unsafe_allow_html=True)

    if not require_director():
        return

    current = get_current_staff()
    tab1, tab2 = st.tabs(["👥 All Staff", "➕ Add Staff Member"])

    with tab1:
        staff_list = get_all_staff()

        if not staff_list:
            st.info("No staff accounts found.")
            return

        for s in staff_list:
            is_self = s['id'] == current.get('id')
            role_badge = "🎯 Director" if s['role'] == 'director' else "👤 Floor Staff"
            status_color = "#7C9A7E" if s['active'] else "#C47B5A"
            status_label = "Active" if s['active'] else "Inactive"

            with st.expander(f"{'🟢' if s['active'] else '🔴'} **{s['full_name']}** (@{s['username']}) — {role_badge}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Role:** {role_badge}")
                    st.markdown(f"**Status:** <span style='color:{status_color};'>{status_label}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Created:** {s['created_at'][:10]}")
                with col2:
                    if is_self:
                        st.info("This is your account.")
                    elif s['active']:
                        with st.form(f"edit_staff_{s['id']}"):
                            new_name = st.text_input("Full Name", value=s['full_name'], key=f"name_{s['id']}")
                            new_role = st.selectbox("Role", ["director", "staff"],
                                                     index=0 if s['role'] == 'director' else 1,
                                                     key=f"role_{s['id']}")
                            new_pw = st.text_input("New Password (leave blank to keep)", type="password", key=f"pw_{s['id']}")
                            col_save, col_deact = st.columns(2)
                            with col_save:
                                if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                                    update_staff(s['id'], new_name, new_role, new_pw if new_pw else None)
                                    st.success("Updated!")
                                    st.rerun()
                            with col_deact:
                                if st.form_submit_button("Deactivate", use_container_width=True):
                                    deactivate_staff(s['id'])
                                    st.warning(f"{s['full_name']} deactivated.")
                                    st.rerun()

    with tab2:
        st.markdown("### Add New Staff Member")

        with st.form("add_staff_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_full_name = st.text_input("Full Name", placeholder="Jane Smith")
                new_username = st.text_input("Username", placeholder="jsmith")
            with col2:
                new_role = st.selectbox("Role", ["staff", "director"],
                                        format_func=lambda x: "Floor Staff" if x == "staff" else "Director")
                new_password = st.text_input("Password", type="password", placeholder="Minimum 8 characters")

            confirm_pw = st.text_input("Confirm Password", type="password")

            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if submitted:
                if not all([new_full_name, new_username, new_password, confirm_pw]):
                    st.error("All fields are required.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                elif new_password != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    try:
                        create_staff(new_username.strip(), new_password, new_role, new_full_name.strip())
                        st.success(f"✅ Account created for {new_full_name}. They can log in with username '{new_username}'.")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE" in str(e):
                            st.error(f"Username '{new_username}' is already taken.")
                        else:
                            st.error(f"Error creating account: {e}")
