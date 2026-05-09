import streamlit as st
from utils.database import get_subscription, authenticate_staff

def check_subscription():
    sub = get_subscription()
    st.session_state.subscription = sub.get("tier", "free")
    st.session_state.facility_name = sub.get("facility_name", "My Facility")
    return sub

def require_pro():
    """Returns True if user has pro or enterprise. Shows upgrade prompt if not."""
    sub = st.session_state.get("subscription", "free")
    if sub in ("pro", "enterprise"):
        return True
    st.warning("⭐ This feature requires a Pro or Enterprise subscription.")
    if st.button("Upgrade Now →", key="upgrade_prompt"):
        st.session_state.page = "Subscription"
        st.rerun()
    return False

def is_pro():
    return st.session_state.get("subscription", "free") in ("pro", "enterprise")

# ---- Staff session helpers ----

def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)

def get_current_staff() -> dict:
    return st.session_state.get("staff", {})

def is_director() -> bool:
    return get_current_staff().get("role") == "director"

def login_staff(username: str, password: str) -> bool:
    staff = authenticate_staff(username, password)
    if staff:
        st.session_state.logged_in = True
        st.session_state.staff = staff
        st.session_state.page = "Dashboard"
        return True
    return False

def logout_staff():
    for key in ["logged_in", "staff"]:
        st.session_state.pop(key, None)
    st.session_state.page = "Dashboard"

def require_director():
    """Returns True if current user is a Director. Shows error if not."""
    if is_director():
        return True
    st.error("🔒 This page requires Director access.")
    return False
