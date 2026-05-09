import streamlit as st
from utils.database import get_subscription

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
