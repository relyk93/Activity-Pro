import streamlit as st
from utils.database import init_db
from utils.auth import check_subscription, is_logged_in, get_current_staff, logout_staff, is_director
from utils.theme import THEMES, DEFAULT_THEME, get_css_variables

st.set_page_config(
    page_title="ActivityPro — Senior Care Calendar",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()
check_subscription()

# ── Theme & emoji defaults ──
if "theme" not in st.session_state:
    st.session_state.theme = DEFAULT_THEME
if "show_emojis" not in st.session_state:
    st.session_state.show_emojis = True

theme = st.session_state.theme
em = st.session_state.show_emojis  # shorthand: True = show emojis

# ── Inject theme CSS variables ──
st.markdown(get_css_variables(theme), unsafe_allow_html=True)

# ── Global CSS (uses var(--ap-*) throughout) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, .stApp {
    background-color: var(--ap-bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ap-text) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--ap-sidebar-bg) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] * { color: var(--ap-sidebar-text) !important; }

/* Headings */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--ap-text) !important;
}

/* Cards */
.ap-card {
    background: var(--ap-surface);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid var(--ap-border);
    box-shadow: 0 2px 12px var(--ap-shadow);
    margin-bottom: 16px;
}
.ap-card-sage {
    background: var(--ap-surface);
    border-left: 4px solid var(--ap-primary);
}
.ap-card-terra {
    background: var(--ap-surface);
    border-left: 4px solid var(--ap-accent);
}
.ap-card-lavender {
    background: var(--ap-surface);
    border-left: 4px solid #9B8EC4;
}
.ap-card-sky {
    background: var(--ap-surface);
    border-left: 4px solid var(--ap-primary-dark);
}

/* Activity category tags */
.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
    letter-spacing: 0.03em;
}
.tag-physical  { background: var(--ap-primary-light); color: var(--ap-primary-dark); }
.tag-cognitive { background: var(--ap-surface-2);     color: var(--ap-primary); }
.tag-social    { background: var(--ap-accent-light);  color: var(--ap-text-mid); }
.tag-creative  { background: var(--ap-surface-3);     color: var(--ap-text-mid); }
.tag-mindful   { background: var(--ap-primary-light); color: var(--ap-primary-dark); }
.tag-special   { background: var(--ap-accent-light);  color: var(--ap-text-mid); }

/* Metric boxes */
.metric-box {
    background: var(--ap-surface);
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    border: 1px solid var(--ap-border);
    box-shadow: 0 1px 6px var(--ap-shadow);
}
.metric-number {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--ap-primary);
}
.metric-label {
    font-size: 0.78rem;
    color: var(--ap-text-light);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

/* Subscription badges */
.sub-badge-free       { background: var(--ap-surface-2); color: var(--ap-text-light); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.sub-badge-pro        { background: linear-gradient(135deg, var(--ap-accent), #FCD34D); color: #1A0A00; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.sub-badge-enterprise { background: linear-gradient(135deg, var(--ap-primary), var(--ap-primary-dark)); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

/* Streamlit buttons */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    background: var(--ap-surface-2) !important;
    color: var(--ap-text) !important;
    border: 1px solid var(--ap-border) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px var(--ap-shadow) !important;
    border-color: var(--ap-primary) !important;
    color: var(--ap-primary) !important;
}
.stButton > button[kind="primary"] {
    background: var(--ap-primary) !important;
    color: white !important;
    border-color: var(--ap-primary) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--ap-primary-dark) !important;
    color: white !important;
}

/* Inputs */
.stTextInput > div, .stTextArea > div, .stSelectbox > div {
    border-radius: 10px !important;
    background: var(--ap-surface) !important;
    border-color: var(--ap-border) !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    background: var(--ap-surface-2) !important;
    border-radius: 10px !important;
    color: var(--ap-text) !important;
}

/* Mobile */
@media (max-width: 768px) {
    .ap-card { padding: 14px !important; }
    .metric-number { font-size: 1.6rem !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
}
@media (max-width: 600px) {
    .stButton > button { min-height: 44px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Login gate ──
if not is_logged_in():
    from pages.login import show as show_login
    show_login()
    st.stop()

# ── Session state defaults ──
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ── Sidebar ──
with st.sidebar:
    # Logo
    logo_emoji = "🌸 " if em else ""
    st.markdown(f"""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-family: Playfair Display, serif; font-size: 1.5rem; font-weight: 700;
                    color: white; letter-spacing: -0.01em;'>{logo_emoji}ActivityPro</div>
        <div style='font-size: 0.7rem; color: var(--ap-sidebar-text); margin-top: 4px;
                    letter-spacing: 0.12em; text-transform: uppercase; opacity: 0.6;'>
            Senior Care Calendar
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Subscription + staff info
    sub = st.session_state.subscription
    badge_map   = {"free": "sub-badge-free", "pro": "sub-badge-pro", "enterprise": "sub-badge-enterprise"}
    badge_label = {"free": "FREE", "pro": ("⭐ " if em else "") + "PRO", "enterprise": ("🏢 " if em else "") + "ENTERPRISE"}
    staff       = get_current_staff()
    role_label  = "Director" if staff.get("role") == "director" else "Floor Staff"
    st.markdown(f"""
    <div style='text-align:center; margin-bottom: 16px;'>
        <span class='{badge_map.get(sub, "sub-badge-free")}'>{badge_label.get(sub, "FREE")}</span>
        <div style='font-size:0.75rem; opacity:0.5; margin-top:6px;'>{st.session_state.facility_name}</div>
        <div style='font-size:0.72rem; opacity:0.4; margin-top:3px;'>
            {staff.get("full_name","?")} · {role_label}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin: 8px 0;'>", unsafe_allow_html=True)

    # ── Navigation ──
    def _nav(icon, label, key):
        prefix = f"{icon} " if em else ""
        return f"{prefix}{label}", key

    all_pages = [
        _nav("🏠", "Dashboard",          "Dashboard"),
        _nav("📋", "Pre-Brief",          "Pre-Brief"),
        _nav("👤", "Resident Cards",     "Resident Cards"),
        _nav("📅", "Calendar",           "Calendar"),
        _nav("🤖", "AI Generator",       "AI Generator"),
        _nav("👥", "Residents",          "Residents"),
        _nav("⭐", "Rate Activities",    "Rate Activities"),
        _nav("📊", "Reports",            "Reports"),
        _nav("🖨️", "Print & Export",    "Print"),
        _nav("👨‍👩‍👧", "Family Updates",  "Family Updates"),
        _nav("🔔", "Notifications",      "Notifications"),
        _nav("⚙️", "Settings",          "Settings"),
        _nav("💳", "Subscription",       "Subscription"),
        _nav("👤", "Staff Management",   "Staff Management"),
    ]
    staff_pages = [
        _nav("🏠", "Dashboard",       "Dashboard"),
        _nav("📋", "Pre-Brief",       "Pre-Brief"),
        _nav("👤", "Resident Cards",  "Resident Cards"),
        _nav("📅", "Calendar",        "Calendar"),
        _nav("⭐", "Rate Activities", "Rate Activities"),
        _nav("👥", "Residents",       "Residents"),
    ]
    pages = all_pages if is_director() else staff_pages

    for label, page_key in pages:
        active = st.session_state.page == page_key
        if st.button(label, key=f"nav_{page_key}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = page_key
            st.rerun()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin: 8px 0;'>", unsafe_allow_html=True)

    # ── Theme & emoji toggles ──
    col_theme, col_emoji = st.columns(2)
    with col_theme:
        is_dark = theme == "dark"
        toggle_label = "☀️ Light" if is_dark else "🌙 Dark"
        if st.button(toggle_label, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()
    with col_emoji:
        emoji_label = "No emoji" if em else "Emojis"
        if st.button(emoji_label, key="emoji_toggle", use_container_width=True):
            st.session_state.show_emojis = not em
            st.rerun()

    # Logout
    logout_label = ("🚪 " if em else "") + "Log Out"
    if st.button(logout_label, key="nav_logout", use_container_width=True):
        logout_staff()
        st.rerun()

    # Free tier upgrade nudge
    if st.session_state.subscription == "free" and is_director():
        lock = "🔒 " if em else ""
        st.markdown(f"""
        <div style='margin-top:16px; padding:12px; background:rgba(245,158,11,0.12);
                    border-radius:10px; border:1px solid rgba(245,158,11,0.25);'>
            <div style='font-size:0.75rem; color:var(--ap-accent); font-weight:600;'>{lock}Upgrade to Pro</div>
            <div style='font-size:0.7rem; opacity:0.5; margin-top:4px;'>AI Generator, Reports & more</div>
        </div>
        """, unsafe_allow_html=True)

# ── Page routing ──
page = st.session_state.page

if   page == "Dashboard":      from pages.dashboard       import show; show()
elif page == "Calendar":       from pages.calendar_view   import show; show()
elif page == "AI Generator":   from pages.ai_generator    import show; show()
elif page == "Residents":      from pages.residents       import show; show()
elif page == "Rate Activities":from pages.rate_activities import show; show()
elif page == "Reports":        from pages.reports         import show; show()
elif page == "Print":          from pages.print_calendar  import show; show()
elif page == "Notifications":  from pages.notifications   import show; show()
elif page == "Settings":       from pages.settings        import show; show()
elif page == "Subscription":   from pages.subscription    import show; show()
elif page == "Staff Management":from pages.staff_management import show; show()
elif page == "Resident Cards": from pages.resident_cards  import show; show()
elif page == "Pre-Brief":      from pages.pre_brief       import show; show()
elif page == "Family Updates": from pages.family_updates  import show; show()
