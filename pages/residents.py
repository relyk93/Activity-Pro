import streamlit as st
from utils.database import get_residents, save_resident, get_engagements, get_conn
from datetime import date

DISABILITY_OPTIONS = [
    "dementia", "alzheimers", "wheelchair", "limited_mobility", "arthritis",
    "hearing_loss", "vision_impairment", "parkinson", "anxiety", "depression",
    "diabetes", "heart_condition", "osteoporosis", "stroke", "autism",
    "dysphagia", "chronic_pain", "incontinence", "fall_risk"
]

DISABILITY_LABELS = {
    "dementia": "🧠 Dementia", "alzheimers": "🧠 Alzheimer's",
    "wheelchair": "♿ Wheelchair User", "limited_mobility": "🦾 Limited Mobility",
    "arthritis": "🤲 Arthritis", "hearing_loss": "👂 Hearing Loss",
    "vision_impairment": "👁 Vision Impairment", "parkinson": "🫀 Parkinson's",
    "anxiety": "💚 Anxiety", "depression": "💙 Depression",
    "diabetes": "🩸 Diabetes", "heart_condition": "❤️ Heart Condition",
    "osteoporosis": "🦴 Osteoporosis", "stroke": "🧬 Stroke History",
    "autism": "🌈 Autism", "dysphagia": "🍴 Dysphagia",
    "chronic_pain": "💊 Chronic Pain", "incontinence": "🚿 Incontinence",
    "fall_risk": "⚠️ Fall Risk", "": "None",
}

def show():
    st.markdown("# 👥 Resident Management")
    tab1, tab2 = st.tabs(["📋 Resident Roster", "➕ Add / Edit Resident"])

    # ─── Tab 1: Roster ───
    with tab1:
        residents = get_residents()
        st.markdown(f"<div style='color:#718096; margin-bottom:16px;'>{len(residents)} active residents</div>", unsafe_allow_html=True)

        # Filter
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_mobility = st.multiselect("Filter by mobility", ["independent", "cane", "walker", "wheelchair"])
        with col_f2:
            filter_disability = st.selectbox("Filter by disability", ["All"] + DISABILITY_OPTIONS)

        filtered = residents
        if filter_mobility:
            filtered = [r for r in filtered if r.get('mobility') in filter_mobility]
        if filter_disability != "All":
            filtered = [r for r in filtered if filter_disability in (r.get('disabilities') or '')]

        for r in filtered:
            disabilities = r.get('disabilities', '') or ''
            disability_tags = ""
            for d in disabilities.split(','):
                d = d.strip()
                if d:
                    label = DISABILITY_LABELS.get(d, d.title())
                    disability_tags += f"<span class='tag tag-mindful' style='margin:2px;'>{label}</span>"

            mobility_icons = {"independent": "🟢", "cane": "🟡", "walker": "🟡", "wheelchair": "🔴"}
            mob_icon = mobility_icons.get(r.get('mobility', 'independent'), "⚪")

            engagements = get_engagements(resident_id=r['id'])
            total_eng = len(engagements)
            engaged_count = sum(1 for e in engagements if e['engaged'])
            eng_rate = int(engaged_count / total_eng * 100) if total_eng > 0 else 0
            eng_color = "#3A6B3A" if eng_rate >= 70 else "#7F5A2A" if eng_rate >= 40 else "#7F2A2A"

            with st.expander(f"{mob_icon} **{r['name']}** · Room {r.get('room','?')} · Age {r.get('age','?')}"):
                col_a, col_b, col_c = st.columns([2, 1, 1])

                with col_a:
                    st.markdown(f"""
                    <div class='ap-card'>
                        <div style='margin-bottom:8px;'><strong>Mobility:</strong> {r.get('mobility','?').title()} &nbsp;|&nbsp; <strong>Cognitive:</strong> {r.get('cognitive','?').replace('_',' ').title()}</div>
                        <div style='margin-bottom:8px;'><strong>Dietary:</strong> {r.get('dietary','None') or 'None'}</div>
                        <div style='margin-bottom:8px;'><strong>Birthday:</strong> {r.get('birthday','Unknown')}</div>
                        <div style='margin-bottom:8px;'><strong>Disabilities / Special Needs:</strong><br>{disability_tags if disability_tags else 'None noted'}</div>
                        <div><strong>Notes:</strong> {r.get('notes','') or '—'}</div>
                        <div style='margin-top:8px;'><strong>Interests:</strong> {r.get('special_needs','') or '—'}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_b:
                    st.markdown(f"""
                    <div class='metric-box'>
                        <div class='metric-number' style='color:{eng_color};'>{eng_rate}%</div>
                        <div class='metric-label'>Engagement Rate</div>
                        <div style='font-size:0.75rem; color:#A0AEC0; margin-top:4px;'>{engaged_count}/{total_eng} activities</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_c:
                    if st.button("✏️ Edit", key=f"edit_res_{r['id']}", use_container_width=True):
                        st.session_state.editing_resident = r
                        st.session_state.active_tab = 1
                        st.rerun()
                    if st.button("📊 History", key=f"hist_res_{r['id']}", use_container_width=True):
                        st.session_state.view_resident_history = r['id']

                # Engagement history
                if st.session_state.get("view_resident_history") == r['id']:
                    st.markdown("#### 📊 Engagement History")
                    if engagements:
                        for eng in engagements[:10]:
                            mood_before = eng.get('mood_before') or 0
                            mood_after = eng.get('mood_after') or 0
                            engaged = "✅ Engaged" if eng['engaged'] else "❌ Did not engage"
                            stars = "⭐" * (eng.get('rating') or 0)
                            st.markdown(f"""
                            <div style='padding:8px 14px; background:#FFFDF9; border-radius:8px; border:1px solid #E2DDD6; margin-bottom:6px; font-size:0.85rem;'>
                                <strong>{eng['event_title']}</strong> — {eng['event_date']}<br>
                                {engaged} &nbsp;|&nbsp; {stars or 'Not rated'} &nbsp;|&nbsp; Mood: {mood_before}→{mood_after}
                                {f"<br><em style='color:#718096;'>{eng['staff_note']}</em>" if eng.get('staff_note') else ''}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No engagement records yet.")
                    if st.button("Close History", key=f"close_hist_{r['id']}"):
                        st.session_state.view_resident_history = None
                        st.rerun()

    # ─── Tab 2: Add/Edit ───
    with tab2:
        editing = st.session_state.get("editing_resident")
        if editing:
            st.markdown(f"### ✏️ Editing: {editing['name']}")
        else:
            st.markdown("### ➕ Add New Resident")

        with st.form("resident_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", value=editing['name'] if editing else "")
                age = st.number_input("Age", min_value=50, max_value=120, value=editing.get('age', 75) if editing else 75)
                room = st.text_input("Room Number", value=editing.get('room','') if editing else "")
                birthday = st.text_input("Birthday (YYYY-MM-DD)", value=editing.get('birthday','') if editing else "")
            with col2:
                mobility = st.selectbox("Mobility Level",
                    ["independent", "cane", "walker", "wheelchair"],
                    index=["independent","cane","walker","wheelchair"].index(editing.get('mobility','independent')) if editing else 0)
                cognitive = st.selectbox("Cognitive Status",
                    ["intact", "mild_impairment", "moderate_impairment", "severe_impairment"],
                    index=["intact","mild_impairment","moderate_impairment","severe_impairment"].index(editing.get('cognitive','intact')) if editing else 0)
                dietary = st.text_input("Dietary Restrictions", value=editing.get('dietary','') if editing else "",
                                        placeholder="e.g. Low sodium, Diabetic, Vegetarian")

            st.markdown("#### ♿ Disabilities & Special Needs")
            st.markdown("<div style='color:#718096; font-size:0.85rem; margin-bottom:8px;'>Select all that apply — the AI will use this to create better activities for this resident.</div>", unsafe_allow_html=True)

            existing_disabilities = []
            if editing and editing.get('disabilities'):
                existing_disabilities = [d.strip() for d in editing['disabilities'].split(',') if d.strip()]

            selected_disabilities = []
            cols = st.columns(3)
            for i, d in enumerate(DISABILITY_OPTIONS):
                with cols[i % 3]:
                    label = DISABILITY_LABELS.get(d, d.title())
                    checked = st.checkbox(label, value=d in existing_disabilities, key=f"disab_{d}")
                    if checked:
                        selected_disabilities.append(d)

            custom_disability = st.text_input("Other disabilities / conditions", placeholder="Add any not listed above")
            if custom_disability:
                selected_disabilities.append(custom_disability)

            special_needs = st.text_input("Interests, hobbies, preferences",
                value=editing.get('special_needs','') if editing else "",
                placeholder="e.g. Loves gardening, used to be a teacher, enjoys 1950s music")
            notes = st.text_area("Staff Notes (private)",
                value=editing.get('notes','') if editing else "",
                placeholder="e.g. Responds well to music, prefers small groups, family visits Sundays")

            col_s, col_c = st.columns(2)
            submitted = col_s.form_submit_button(
                "Update Resident" if editing else "Add Resident",
                type="primary", use_container_width=True)
            cancelled = col_c.form_submit_button("Cancel", use_container_width=True)

            if submitted and name:
                data = {
                    "name": name, "age": int(age), "room": room, "birthday": birthday,
                    "mobility": mobility, "cognitive": cognitive, "dietary": dietary,
                    "disabilities": ",".join(selected_disabilities),
                    "special_needs": special_needs, "notes": notes
                }
                save_resident(data, resident_id=editing['id'] if editing else None)
                st.success(f"✅ {'Updated' if editing else 'Added'} {name}!")
                st.session_state.editing_resident = None
                st.rerun()

            if cancelled:
                st.session_state.editing_resident = None
                st.rerun()
