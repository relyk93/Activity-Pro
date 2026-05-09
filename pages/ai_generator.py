import streamlit as st
import json
import requests
from utils.auth import require_pro
from utils.database import get_residents, save_activity, save_event, get_activities
from datetime import date, timedelta

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def call_claude(prompt, system_prompt):
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("Missing ANTHROPIC_API_KEY in .streamlit/secrets.toml")
        return None

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    try:
        resp = requests.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=60)
    except requests.RequestException as exc:
        st.error(f"AI request failed: {exc}")
        return None

    if resp.status_code == 200:
        data = resp.json()
        return data["content"][0]["text"]

    error_body = resp.text[:500]
    st.error(f"Anthropic API error ({resp.status_code}): {error_body}")
    return None

def show():
    st.markdown("# 🤖 AI Activity Generator")
    st.markdown("<div style='color:#718096; margin-bottom:20px;'>Powered by Claude — your expert AI activity director</div>", unsafe_allow_html=True)

    if not require_pro():
        return

    tab1, tab2, tab3 = st.tabs(["📅 Generate Weekly Calendar", "✨ Generate Single Activity", "🔧 Customize for Residents"])

    # ─── Tab 1: Weekly Calendar ───
    with tab1:
        st.markdown("### Generate a Full Week of Activities")
        st.markdown("The AI will create a balanced, personalized weekly calendar based on your residents' needs.")

        residents = get_residents()
        all_disabilities = set()
        for r in residents:
            if r.get('disabilities'):
                for d in r['disabilities'].split(','):
                    d = d.strip()
                    if d:
                        all_disabilities.add(d)

        col1, col2 = st.columns(2)
        with col1:
            week_start = st.date_input("Week Starting", value=date.today() - timedelta(days=date.today().weekday()))
            daily_count = st.slider("Activities per day", 2, 5, 3)
            include_special = st.checkbox("Include special needs group activities", value=True)
        with col2:
            focus_areas = st.multiselect("Focus areas this week",
                ["Physical", "Mindful", "Social", "Cognitive", "Creative"],
                default=["Physical", "Mindful", "Social"])
            budget = st.selectbox("Weekly budget", ["Free / No Cost", "Under $20", "Under $50", "No limit"])
            special_occasions = st.text_input("Any special occasions this week?", placeholder="e.g. Margaret's birthday, Fall theme")

        existing_activities = get_activities()
        existing_titles = [a['title'] for a in existing_activities]

        if st.button("🤖 Generate Weekly Calendar", type="primary", use_container_width=True):
            disabilities_list = ", ".join(all_disabilities) if all_disabilities else "None noted"
            resident_summary = f"{len(residents)} residents aged 60+. Disabilities present: {disabilities_list}."

            system_prompt = """You are an expert senior activity director with 20+ years of experience.
You specialize in creating engaging, therapeutic, and joyful activities for seniors aged 60+.
You deeply understand dementia care, mobility limitations, sensory impairments, and emotional wellbeing.
You always design activities that are:
- Safe and accessible for varying ability levels
- Low-cost and easy to prepare
- Emotionally meaningful and dignity-preserving
- Balanced across physical, cognitive, social, creative, and mindful categories
- Evidence-based for senior wellbeing
Respond ONLY with valid JSON, no markdown, no extra text."""

            prompt = f"""Create a complete weekly activity calendar for a senior living facility.

Resident profile: {resident_summary}
Week starting: {week_start}
Activities per day: {daily_count}
Focus areas: {', '.join(focus_areas)}
Budget: {budget}
Special occasions: {special_occasions if special_occasions else 'None'}
Include special needs activities: {include_special}
Avoid duplicating these existing activities: {', '.join(existing_titles[:20])}

Return a JSON object with this exact structure:
{{
  "week_theme": "theme name",
  "days": [
    {{
      "date": "YYYY-MM-DD",
      "day_name": "Monday",
      "activities": [
        {{
          "title": "Activity Name",
          "time": "10:00 AM",
          "category": "physical|mindful|social|cognitive|creative",
          "group_type": "all|special_needs",
          "duration_minutes": 45,
          "cost_estimate": "Free",
          "description": "Brief engaging description",
          "instructions": "Step 1: ...\\nStep 2: ...\\nStep 3: ...",
          "supplies": "Item 1, Item 2, Item 3",
          "disability_friendly": "wheelchair,dementia,arthritis",
          "location": "Activity Room"
        }}
      ]
    }}
  ]
}}"""

            with st.spinner("🌸 Your AI activity director is crafting the perfect week..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    calendar_data = json.loads(clean)
                    st.session_state.generated_calendar = calendar_data
                    st.session_state.week_start_for_save = week_start
                    st.success(f"✅ Generated calendar: **{calendar_data.get('week_theme', 'Weekly Activities')}**")
                except Exception as e:
                    st.error(f"Could not parse AI response. Please try again. ({e})")
            else:
                st.error("API call failed. Please check your connection.")

        # Preview & save
        if st.session_state.get("generated_calendar"):
            cal = st.session_state.generated_calendar
            st.markdown(f"### 🗓 Preview: {cal.get('week_theme', 'Weekly Calendar')}")

            for day in cal.get("days", []):
                with st.expander(f"**{day['day_name']} — {day['date']}** ({len(day['activities'])} activities)"):
                    for act in day['activities']:
                        cat = act.get('category', 'social')
                        group = act.get('group_type', 'all')
                        is_special = group == 'special_needs'
                        st.markdown(f"""
                        <div class='ap-card {"ap-card-lavender" if is_special else "ap-card-sage"}' style='margin-bottom:12px;'>
                            <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                                <div>
                                    <strong style='font-size:1.05rem;'>{'🟣 ' if is_special else ''}{act['title']}</strong>
                                    <div style='color:#718096; font-size:0.85rem; margin-top:3px;'>
                                        🕐 {act.get('time','TBD')} · ⏱ {act.get('duration_minutes',60)}min · 💰 {act.get('cost_estimate','Free')} · 📍 {act.get('location','Activity Room')}
                                    </div>
                                    <div style='margin-top:6px; color:#4A5568;'>{act.get('description','')}</div>
                                </div>
                                <span class='tag tag-{cat}'>{cat.title()}</span>
                            </div>
                            <div style='margin-top:10px;'>
                                <strong style='font-size:0.8rem; color:#718096;'>SUPPLIES:</strong>
                                <span style='font-size:0.85rem; color:#4A5568;'> {act.get('supplies','None needed')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            col_save, col_discard = st.columns(2)
            with col_save:
                if st.button("💾 Save Entire Week to Calendar", type="primary", use_container_width=True):
                    saved_count = 0
                    for day in cal.get("days", []):
                        for act in day.get("activities", []):
                            act_id = save_activity({
                                "title": act['title'],
                                "description": act.get('description', ''),
                                "instructions": act.get('instructions', ''),
                                "supplies": act.get('supplies', ''),
                                "category": act.get('category', 'social'),
                                "duration_minutes": act.get('duration_minutes', 60),
                                "cost_estimate": act.get('cost_estimate', 'Free'),
                                "difficulty": "easy",
                                "group_type": act.get('group_type', 'all'),
                                "disability_friendly": act.get('disability_friendly', ''),
                                "is_special_needs": 1 if act.get('group_type') == 'special_needs' else 0,
                                "created_by": "AI",
                            })
                            save_event({
                                "activity_id": act_id,
                                "title": act['title'],
                                "date": day['date'],
                                "time": act.get('time', '10:00 AM'),
                                "location": act.get('location', 'Activity Room'),
                                "group_type": act.get('group_type', 'all'),
                                "notes": "",
                            })
                            saved_count += 1
                    st.success(f"✅ {saved_count} activities saved to your calendar!")
                    st.session_state.generated_calendar = None
                    st.rerun()
            with col_discard:
                if st.button("🗑 Discard", use_container_width=True):
                    st.session_state.generated_calendar = None
                    st.rerun()

    # ─── Tab 2: Single Activity ───
    with tab2:
        st.markdown("### Generate One Custom Activity")
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", ["Physical", "Mindful", "Social", "Cognitive", "Creative"])
            group = st.radio("Group", ["All Residents", "Special Needs Group"])
            duration = st.slider("Duration (minutes)", 15, 120, 45)
        with col2:
            budget_single = st.selectbox("Max cost", ["Free", "Under $5", "Under $15", "Under $30"])
            disabilities_focus = st.multiselect("Optimize for disabilities",
                ["Dementia", "Wheelchair", "Arthritis", "Hearing Loss", "Vision Impairment",
                 "Parkinson's", "Anxiety", "Depression", "Limited Mobility"])
            extra_notes = st.text_area("Any special requests?", placeholder="e.g. Focus on music, good for summer, involves food...")

        if st.button("✨ Generate Activity", type="primary"):
            system_prompt = """You are an expert senior activity director. Generate detailed, practical, engaging activities.
Respond ONLY with valid JSON, no markdown fences, no extra text."""
            prompt = f"""Generate one senior activity with these parameters:
Category: {category}
Group: {group}
Duration: {duration} minutes
Budget: {budget_single}
Disabilities to consider: {', '.join(disabilities_focus) if disabilities_focus else 'General population'}
Special requests: {extra_notes if extra_notes else 'None'}

Return JSON:
{{
  "title": "Activity Name",
  "description": "Engaging 2-3 sentence description",
  "instructions": "Step 1: ...\\nStep 2: ...\\nStep 3: ...\\n(8-12 detailed steps)",
  "supplies": "Comma-separated supply list with estimated costs",
  "category": "{category.lower()}",
  "duration_minutes": {duration},
  "cost_estimate": "{budget_single}",
  "difficulty": "easy",
  "group_type": "{'special_needs' if 'Special' in group else 'all'}",
  "disability_friendly": "comma,separated,disability,tags",
  "tips": "3-4 expert tips for facilitating this activity"
}}"""

            with st.spinner("Creating your perfect activity..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    act = json.loads(clean)
                    st.session_state.single_activity = act
                except:
                    st.error("Could not parse response. Try again.")

        if st.session_state.get("single_activity"):
            act = st.session_state.single_activity
            st.markdown(f"""
            <div class='ap-card ap-card-sage'>
                <h2 style='margin:0 0 8px 0;'>{act['title']}</h2>
                <p style='color:#4A5568;'>{act.get('description','')}</p>
                <hr style='margin:12px 0;'>
                <strong>📝 Instructions:</strong>
                <pre style='font-family:DM Sans,sans-serif; white-space:pre-wrap; color:#1A2332; margin-top:8px;'>{act.get('instructions','')}</pre>
                <hr style='margin:12px 0;'>
                <strong>🛒 Supplies:</strong> {act.get('supplies','')}
                <br><strong>💡 Expert Tips:</strong> {act.get('tips','')}
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save Activity", type="primary", use_container_width=True):
                    save_activity(act)
                    st.success(f"✅ '{act['title']}' saved to your activity library!")
                    st.session_state.single_activity = None
            with c2:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.single_activity = None
                    st.rerun()

    # ─── Tab 3: Personalized for Resident ───
    with tab3:
        st.markdown("### Generate Activities Personalized for a Specific Resident")
        residents = get_residents()
        if not residents:
            st.info("Add residents first to use this feature.")
            return

        resident_map = {r['name']: r for r in residents}
        selected_name = st.selectbox("Select Resident", list(resident_map.keys()))
        resident = resident_map[selected_name]

        st.markdown(f"""
        <div class='ap-card ap-card-sky' style='margin:12px 0;'>
            <strong>{resident['name']}</strong> · Age {resident.get('age','?')} · Room {resident.get('room','?')}<br>
            <span style='color:#718096; font-size:0.85rem;'>
                Mobility: {resident.get('mobility','?')} · Cognitive: {resident.get('cognitive','?')}<br>
                Disabilities: {resident.get('disabilities','None') or 'None'}<br>
                Interests/Notes: {resident.get('special_needs','None') or 'None'}
            </span>
        </div>
        """, unsafe_allow_html=True)

        num_activities = st.slider("Number of activities to generate", 1, 5, 3)

        if st.button("🎯 Generate Personalized Activities", type="primary"):
            system_prompt = """You are a compassionate expert senior activity director.
Generate activities perfectly suited to an individual resident's abilities, interests, and needs.
Respond ONLY with valid JSON array, no markdown, no extra text."""

            prompt = f"""Generate {num_activities} personalized activities for this resident:

Name: {resident['name']}
Age: {resident.get('age', 'Unknown')}
Mobility: {resident.get('mobility', 'independent')}
Cognitive status: {resident.get('cognitive', 'intact')}
Disabilities: {resident.get('disabilities', 'None')}
Dietary restrictions: {resident.get('dietary', 'None')}
Interests & notes: {resident.get('special_needs', '') + ' ' + resident.get('notes', '')}

Create activities that work WITH their limitations, not around them. 
Make them meaningful, dignified, and joyful for THIS specific person.

Return a JSON array:
[
  {{
    "title": "Activity Name",
    "why_this_works": "1-2 sentences explaining why this suits {resident['name']} specifically",
    "description": "Description",
    "instructions": "Step 1: ...\\nStep 2: ...",
    "supplies": "Supply list",
    "category": "physical|mindful|social|cognitive|creative",
    "duration_minutes": 30,
    "cost_estimate": "Free",
    "difficulty": "easy",
    "group_type": "all",
    "disability_friendly": "relevant,disability,tags",
    "adaptations": "Specific adaptations made for this resident"
  }}
]"""

            with st.spinner(f"Crafting personalized activities for {resident['name']}..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    activities = json.loads(clean)
                    st.session_state.personalized_activities = activities
                    st.session_state.personalized_for = resident['name']
                except:
                    st.error("Could not parse response.")

        if st.session_state.get("personalized_activities"):
            acts = st.session_state.personalized_activities
            st.markdown(f"### 🎯 Activities for {st.session_state.get('personalized_for','')}")
            for i, act in enumerate(acts):
                with st.expander(f"**{act['title']}** — {act.get('category','').title()} · {act.get('duration_minutes',30)} min"):
                    st.markdown(f"""
                    <div class='ap-card ap-card-lavender'>
                        <div style='background:#E8FFEA; border-radius:8px; padding:10px; margin-bottom:12px; border-left:3px solid #3A6B3A;'>
                            <strong style='color:#3A6B3A;'>💚 Why this works:</strong> {act.get('why_this_works','')}
                        </div>
                        <p>{act.get('description','')}</p>
                        <strong>Instructions:</strong>
                        <pre style='font-family:DM Sans,sans-serif; white-space:pre-wrap;'>{act.get('instructions','')}</pre>
                        <strong>Supplies:</strong> {act.get('supplies','')}
                        <br><strong>Adaptations:</strong> {act.get('adaptations','')}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"💾 Save Activity #{i+1}", key=f"save_personal_{i}"):
                        act['is_special_needs'] = 0
                        save_activity(act)
                        st.success(f"Saved '{act['title']}'!")
