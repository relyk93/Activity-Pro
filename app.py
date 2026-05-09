import streamlit as st
from utils.database import init_db
from utils.auth import check_subscription, is_logged_in, get_current_staff, logout_staff, is_director

st.set_page_config(
    page_title="ActivityPro — Senior Care Calendar",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()
check_subscription()

# Login gate — show login page if not authenticated
if not is_logged_in():
    from pages.login import show as show_login
    show_login()
    st.stop()

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* Root variables */
:root {
    --sage: #7C9A7E;
    --sage-light: #A8C5AA;
    --sage-dark: #4A6B4C;
    --cream: #FAF7F2;
    --warm-white: #FFFDF9;
    --terracotta: #C47B5A;
    --terracotta-light: #E8A98A;
    --navy: #2C3E50;
    --gold: #D4A843;
    --lavender: #9B8EC4;
    --sky: #6BA3BE;
    --text-dark: #1A2332;
    --text-mid: #4A5568;
    --text-light: #718096;
    --border: #E2DDD6;
    --shadow: rgba(44, 62, 80, 0.08);
}

html, body, .stApp {
    background-color: var(--cream) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--navy) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * {
    color: #E8EDF2 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 6px 0 !important;
}

/* Headings */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--text-dark) !important;
}

/* Cards */
.ap-card {
    background: var(--warm-white);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid var(--border);
    box-shadow: 0 2px 12px var(--shadow);
    margin-bottom: 16px;
}

.ap-card-sage {
    background: linear-gradient(135deg, #EEF5EE 0%, #F5F9F5 100%);
    border-left: 4px solid var(--sage);
}

.ap-card-terra {
    background: linear-gradient(135deg, #FBF0EA 0%, #FEF5F0 100%);
    border-left: 4px solid var(--terracotta);
}

.ap-card-lavender {
    background: linear-gradient(135deg, #F0EDF8 0%, #F6F4FB 100%);
    border-left: 4px solid var(--lavender);
}

.ap-card-sky {
    background: linear-gradient(135deg, #EAF3F8 0%, #F0F7FB 100%);
    border-left: 4px solid var(--sky);
}

/* Activity tags */
.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
    letter-spacing: 0.03em;
}
.tag-physical { background: #DEF0DE; color: #3A6B3A; }
.tag-cognitive { background: #DDE8F5; color: #2A4A7F; }
.tag-social { background: #F5DDDE; color: #7F2A2E; }
.tag-creative { background: #F5EDDD; color: #7F5A2A; }
.tag-mindful { background: #EBE4F5; color: #5A3A7F; }
.tag-special { background: #F5F0DD; color: #7F6A2A; }

/* Metric boxes */
.metric-box {
    background: var(--warm-white);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid var(--border);
}
.metric-number {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--sage-dark);
}
.metric-label {
    font-size: 0.8rem;
    color: var(--text-light);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

/* Subscription badge */
.sub-badge-free { background: #F0F0F0; color: #666; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.sub-badge-pro { background: linear-gradient(135deg, #D4A843, #E8C063); color: #5A3A00; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.sub-badge-enterprise { background: linear-gradient(135deg, #7C9A7E, #9BB89D); color: #1A3A1C; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

/* Buttons */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    border: none !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .ap-card { padding: 14px !important; }
    .metric-number { font-size: 1.6rem !important; }
    [data-testid="stSidebar"] { min-width: 240px !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    .stButton > button { font-size: 0.85rem !important; padding: 8px 12px !important; }
}

/* Touch-friendly buttons on mobile */
@media (max-width: 600px) {
    .stButton > button { min-height: 44px !important; }
    .stSelectbox, .stTextInput { font-size: 16px !important; }
}


/* Selectbox, inputs */
.stSelectbox > div, .stTextInput > div, .stTextArea > div {
    border-radius: 10px !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    background: var(--warm-white) !important;
    border-radius: 10px !important;
}

/* Activity rating stars */
.star-rating { font-size: 1.4rem; letter-spacing: 4px; }
</style>
""", unsafe_allow_html=True)

# Session state defaults
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# Sidebar navigation
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-family: Playfair Display, serif; font-size: 1.6rem; font-weight: 700; color: #FAF7F2;'>🌸 ActivityPro</div>
        <div style='font-size: 0.75rem; color: #A0AEC0; margin-top: 4px; letter-spacing: 0.1em; text-transform: uppercase;'>Senior Care Calendar</div>
    </div>
    """, unsafe_allow_html=True)

    sub = st.session_state.subscription
    badge_map = {"free": "sub-badge-free", "pro": "sub-badge-pro", "enterprise": "sub-badge-enterprise"}
    badge_label = {"free": "FREE TIER", "pro": "⭐ PRO", "enterprise": "🏢 ENTERPRISE"}
    staff = get_current_staff()
    role_label = "Director" if staff.get("role") == "director" else "Floor Staff"
    st.markdown(f"""
    <div style='text-align:center; margin-bottom: 20px;'>
        <span class='{badge_map.get(sub, "sub-badge-free")}'>{badge_label.get(sub, "FREE")}</span>
        <div style='font-size:0.75rem; color:#718096; margin-top:6px;'>{st.session_state.facility_name}</div>
        <div style='font-size:0.72rem; color:#A0AEC0; margin-top:4px;'>👤 {staff.get("full_name","?")} · {role_label}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Directors see all pages; Floor Staff see a limited set
    all_pages = {
        "🏠 Dashboard": "Dashboard",
        "📋 Pre-Brief": "Pre-Brief",
        "👤 Resident Cards": "Resident Cards",
        "📅 Calendar": "Calendar",
        "🤖 AI Activity Generator": "AI Generator",
        "👥 Residents": "Residents",
        "⭐ Rate Activities": "Rate Activities",
        "📊 Reports": "Reports",
        "🖨️ Print & Export": "Print",
        "👨‍👩‍👧 Family Updates": "Family Updates",
        "🔔 Notifications": "Notifications",
        "⚙️ Settings": "Settings",
        "💳 Subscription": "Subscription",
        "👤 Staff Management": "Staff Management",
    }
    staff_pages = {
        "🏠 Dashboard": "Dashboard",
        "📋 Pre-Brief": "Pre-Brief",
        "👤 Resident Cards": "Resident Cards",
        "📅 Calendar": "Calendar",
        "⭐ Rate Activities": "Rate Activities",
        "👥 Residents": "Residents",
    }
    pages = all_pages if is_director() else staff_pages

    for label, page_key in pages.items():
        if st.button(label, key=f"nav_{page_key}", use_container_width=True):
            st.session_state.page = page_key

    st.markdown("---")
    if st.button("🚪 Log Out", key="nav_logout", use_container_width=True):
        logout_staff()
        st.rerun()

    # Lock indicators for free tier
    if st.session_state.subscription == "free" and is_director():
        st.markdown("""
        <div style='margin-top: 20px; padding: 12px; background: rgba(212,168,67,0.15); border-radius: 10px; border: 1px solid rgba(212,168,67,0.3);'>
            <div style='font-size: 0.75rem; color: #D4A843; font-weight: 600;'>🔒 Upgrade to Pro</div>
            <div style='font-size: 0.7rem; color: #A0AEC0; margin-top: 4px;'>AI Generator, Reports & more</div>
        </div>
        """, unsafe_allow_html=True)

# Route to pages
page = st.session_state.page

if page == "Dashboard":
    from pages.dashboard import show
    show()
elif page == "Calendar":
    from pages.calendar_view import show
    show()
elif page == "AI Generator":
    from pages.ai_generator import show
    show()
elif page == "Residents":
    from pages.residents import show
    show()
elif page == "Rate Activities":
    from pages.rate_activities import show
    show()
elif page == "Reports":
    from pages.reports import show
    show()
elif page == "Print":
    from pages.print_calendar import show
    show()
elif page == "Notifications":
    from pages.notifications import show
    show()
elif page == "Settings":
    from pages.settings import show
    show()
elif page == "Subscription":
    from pages.subscription import show
    show()
elif page == "Staff Management":
    from pages.staff_management import show
    show()
elif page == "Resident Cards":
    from pages.resident_cards import show
    show()
elif page == "Pre-Brief":
    from pages.pre_brief import show
    show()
elif page == "Family Updates":
    from pages.family_updates import show
    show()
