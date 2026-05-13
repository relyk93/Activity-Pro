import streamlit as st
import json
import requests
from utils.auth import require_pro
from utils.database import (get_residents, save_activity, save_event,
                             get_activities, get_activity_ratings_summary,
                             get_resident_interests)
from datetime import date, timedelta

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def call_claude(prompt, system_prompt):
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        st.error("Missing ANTHROPIC_API_KEY in .streamlit/secrets.toml")
        return None

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}],
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
        return resp.json()["content"][0]["text"]
    st.error(f"Anthropic API error ({resp.status_code}): {resp.text[:300]}")
    return None


def generate_activity_image(activity_title: str, category: str, description: str) -> str | None:
    """Generate an activity image via DALL-E 3. Returns image URL or None."""
    try:
        openai_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        openai_key = ""
    if not openai_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        prompt = (
            f"A warm, joyful photograph of elderly seniors in a senior living facility doing "
            f"'{activity_title}'. {description} "
            f"The atmosphere is welcoming and dignified. Bright natural light, candid smiles, "
            f"caring staff nearby. Photorealistic, optimistic, heartwarming. "
            f"No text, no logos."
        )
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x576",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception:
        return None


def _interests_section(residents):
    """Render the resident interests panel and return selected interests."""
    all_interests = get_resident_interests()
    # Also pull structured interests from special_needs field
    structured = set()
    for r in residents:
        if r.get('special_needs'):
            for i in r['special_needs'].split(','):
                i = i.strip()
                if i:
                    structured.add(i.title())

    combined = sorted(set(all_interests) | structured)

    st.markdown("**Resident Interest Pool**")
    st.caption("Pulled from all resident profiles. Select which to prioritise this week.")
    if combined:
        selected = st.multiselect(
            "Focus on these interests",
            options=combined,
            default=combined[:min(6, len(combined))],
            key="interest_pool",
        )
    else:
        selected = []
        st.info("Add interests to resident profiles to use this feature.")
    return selected


def show():
    st.markdown("# 🤖 AI Activity Generator")
    st.markdown(
        "<div style='color:var(--ap-text-light); margin-bottom:20px;'>"
        "Powered by Claude AI — personalised to your residents' real interests and past ratings."
        "</div>",
        unsafe_allow_html=True,
    )

    if not require_pro():
        return

    tab1, tab2, tab3 = st.tabs(
        ["📅 Generate Weekly Calendar", "✨ Generate Single Activity", "🔧 Customize for Residents"]
    )

    # ─── Tab 1: Weekly Calendar ───
    with tab1:
        st.markdown("### Generate a Full Week of Activities")

        residents = get_residents()
        liked_activities, disliked_activities = get_activity_ratings_summary()
        all_disabilities = set()
        for r in residents:
            if r.get('disabilities'):
                for d in r['disabilities'].split(','):
                    d = d.strip()
                    if d:
                        all_disabilities.add(d)

        col1, col2 = st.columns(2)
        with col1:
            week_start = st.date_input(
                "Week Starting",
                value=date.today() - timedelta(days=date.today().weekday()),
            )
            daily_count = st.slider("Activities per day", 2, 5, 3)
            include_special = st.checkbox("Include special needs group activities", value=True)
            special_occasions = st.text_input(
                "Special occasions this week?",
                placeholder="e.g. Margaret's birthday, Fall theme",
            )

        with col2:
            focus_areas = st.multiselect(
                "Focus areas",
                ["Physical", "Mindful", "Social", "Cognitive", "Creative", "Photo & Memory"],
                default=["Physical", "Mindful", "Social"],
            )
            budget = st.selectbox(
                "Weekly budget",
                ["Free / No Cost", "Under $20", "Under $50", "No limit"],
            )
            allow_repeats = st.checkbox(
                "Allow repeating highly-rated activities",
                value=True,
                help="Activities your residents rated 3.5★+ can be suggested again.",
            )

        # Interests panel
        selected_interests = _interests_section(residents)

        # Ratings summary callout
        if liked_activities or disliked_activities:
            with st.expander("📊 Ratings intelligence — what the AI will use", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Residents loved these** ✅")
                    for a in liked_activities[:8]:
                        st.markdown(f"- {a}")
                    if not liked_activities:
                        st.caption("Not enough data yet.")
                with c2:
                    st.markdown("**Skip or rethink these** ❌")
                    for a in disliked_activities[:8]:
                        st.markdown(f"- {a}")
                    if not disliked_activities:
                        st.caption("No low-rated activities yet.")

        existing_titles = [a['title'] for a in get_activities()]

        if st.button("🤖 Generate Weekly Calendar", type="primary", use_container_width=True):
            disabilities_list = ", ".join(all_disabilities) if all_disabilities else "None noted"
            resident_summary = (
                f"{len(residents)} residents aged 60+. "
                f"Disabilities present: {disabilities_list}."
            )
            interests_str = ", ".join(selected_interests) if selected_interests else "General interests"
            liked_str = ", ".join(liked_activities[:10]) if liked_activities else "None yet"
            disliked_str = ", ".join(disliked_activities[:10]) if disliked_activities else "None"
            repeat_instruction = (
                f"You MAY suggest repeating these highly-rated activities if appropriate: {liked_str}."
                if allow_repeats
                else "Do NOT repeat any existing activities."
            )

            system_prompt = """You are an expert senior activity director with 20+ years of experience.
You create engaging, therapeutic, joyful activities for seniors aged 60+.
You deeply understand dementia care, mobility limitations, sensory impairments, and emotional wellbeing.
Always design activities that are safe, low-cost, emotionally meaningful, dignity-preserving, and evidence-based.
Respond ONLY with valid JSON, no markdown, no extra text."""

            prompt = f"""Create a complete weekly activity calendar for a senior living facility.

Resident profile: {resident_summary}
Resident interests to incorporate: {interests_str}
Week starting: {week_start}
Activities per day: {daily_count}
Focus areas: {', '.join(focus_areas)}
Budget: {budget}
Special occasions: {special_occasions if special_occasions else 'None'}
Include special needs activities: {include_special}

RATINGS INTELLIGENCE — use this to personalise the calendar:
- Residents loved these activities (safe to repeat if allowed): {liked_str}
- Residents did NOT engage well with these — avoid or significantly modify: {disliked_str}
- {repeat_instruction}
- Avoid duplicating these existing activities (unless in liked list): {', '.join(existing_titles[:20])}

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
          "location": "Activity Room",
          "interest_connection": "Which resident interests this serves"
        }}
      ]
    }}
  ]
}}"""

            with st.spinner("🌸 Crafting your personalised week..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    calendar_data = json.loads(clean)
                    st.session_state.generated_calendar = calendar_data
                    st.session_state.week_start_for_save = week_start
                    st.success(f"✅ Generated: **{calendar_data.get('week_theme', 'Weekly Activities')}**")
                except Exception as e:
                    st.error(f"Could not parse AI response. Please try again. ({e})")
            else:
                st.error("API call failed. Please check your connection.")

        # Preview & save
        if st.session_state.get("generated_calendar"):
            cal = st.session_state.generated_calendar
            st.markdown(f"### 🗓 Preview: {cal.get('week_theme', 'Weekly Calendar')}")

            for day in cal.get("days", []):
                with st.expander(
                    f"**{day['day_name']} — {day['date']}** ({len(day['activities'])} activities)"
                ):
                    for act in day['activities']:
                        cat = act.get('category', 'social')
                        is_special = act.get('group_type') == 'special_needs'
                        interest_note = act.get('interest_connection', '')
                        st.markdown(f"""
                        <div class='ap-card {"ap-card-lavender" if is_special else "ap-card-sage"}' style='margin-bottom:12px;'>
                            <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                                <div>
                                    <strong style='font-size:1.05rem;'>{'🟣 ' if is_special else ''}{act['title']}</strong>
                                    <div style='color:var(--ap-text-light); font-size:0.82rem; margin-top:3px;'>
                                        🕐 {act.get('time','TBD')} · ⏱ {act.get('duration_minutes',60)} min ·
                                        💰 {act.get('cost_estimate','Free')} · 📍 {act.get('location','Activity Room')}
                                    </div>
                                    <div style='margin-top:6px; color:var(--ap-text-mid);'>{act.get('description','')}</div>
                                    {f"<div style='margin-top:6px; font-size:0.8rem; color:var(--ap-primary);'>🎯 {interest_note}</div>" if interest_note else ""}
                                </div>
                                <span class='tag tag-{cat}'>{cat.title()}</span>
                            </div>
                            <div style='margin-top:10px;'>
                                <strong style='font-size:0.8rem; color:var(--ap-text-light);'>SUPPLIES:</strong>
                                <span style='font-size:0.85rem;'> {act.get('supplies','None needed')}</span>
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

        residents = get_residents()
        liked_activities, disliked_activities = get_activity_ratings_summary()
        all_interests = get_resident_interests()

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Category",
                ["Physical", "Mindful", "Social", "Cognitive", "Creative", "Photo & Memory"],
            )
            group = st.radio("Group", ["All Residents", "Special Needs Group"])
            duration = st.slider("Duration (minutes)", 15, 120, 45)

        with col2:
            budget_single = st.selectbox("Max cost", ["Free", "Under $5", "Under $15", "Under $30"])
            disabilities_focus = st.multiselect(
                "Optimise for disabilities",
                ["Dementia", "Wheelchair", "Arthritis", "Hearing Loss", "Vision Impairment",
                 "Parkinson's", "Anxiety", "Depression", "Limited Mobility"],
            )
            interest_focus = st.multiselect(
                "Incorporate these interests",
                options=all_interests,
                default=all_interests[:3] if all_interests else [],
            )

        extra_notes = st.text_area(
            "Any special requests?",
            placeholder="e.g. Good for summer, involves food, works well outdoors...",
        )

        generate_image = st.checkbox(
            "Generate activity image with AI 🖼",
            value=False,
            help="Requires OPENAI_API_KEY in secrets.toml. Uses DALL-E 3.",
        )

        if st.button("✨ Generate Activity", type="primary"):
            liked_str = ", ".join(liked_activities[:8]) if liked_activities else "None yet"
            disliked_str = ", ".join(disliked_activities[:8]) if disliked_activities else "None"
            interest_str = ", ".join(interest_focus) if interest_focus else "General"

            system_prompt = """You are an expert senior activity director. Generate detailed, practical, engaging activities.
Respond ONLY with valid JSON, no markdown fences, no extra text."""

            prompt = f"""Generate one senior activity:
Category: {category}
Group: {group}
Duration: {duration} minutes
Budget: {budget_single}
Disabilities to consider: {', '.join(disabilities_focus) if disabilities_focus else 'General'}
Resident interests to incorporate: {interest_str}
Avoid activities residents disliked: {disliked_str}
Extra notes: {extra_notes if extra_notes else 'None'}

Return JSON:
{{
  "title": "Activity Name",
  "description": "Engaging 2-3 sentence description mentioning how it connects to resident interests",
  "instructions": "Step 1: ...\\nStep 2: ...\\n(8-12 detailed steps)",
  "supplies": "Comma-separated supply list",
  "category": "{category.lower().replace(' & ', '_')}",
  "duration_minutes": {duration},
  "cost_estimate": "{budget_single}",
  "difficulty": "easy",
  "group_type": "{'special_needs' if 'Special' in group else 'all'}",
  "disability_friendly": "comma,separated,disability,tags",
  "interest_connection": "Which resident interests this serves and how",
  "tips": "3-4 expert facilitation tips",
  "image_prompt": "A detailed DALL-E prompt for a photo of seniors doing this activity in a warm senior care setting"
}}"""

            with st.spinner("Creating your activity..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    act = json.loads(clean)
                    st.session_state.single_activity = act
                except Exception:
                    st.error("Could not parse response. Try again.")

        if st.session_state.get("single_activity"):
            act = st.session_state.single_activity

            # Optionally generate image
            img_url = None
            if generate_image:
                with st.spinner("🖼 Generating activity image with DALL-E..."):
                    img_url = generate_activity_image(
                        act['title'],
                        act.get('category', ''),
                        act.get('description', ''),
                    )
                if not img_url:
                    st.caption("Image generation skipped — add OPENAI_API_KEY to secrets.toml to enable.")

            if img_url:
                st.image(img_url, caption=act['title'], use_container_width=True)

            interest_note = act.get('interest_connection', '')
            st.markdown(f"""
            <div class='ap-card ap-card-sage'>
                <h2 style='margin:0 0 6px 0;'>{act['title']}</h2>
                <p style='color:var(--ap-text-mid);'>{act.get('description','')}</p>
                {f"<div style='margin:8px 0; font-size:0.85rem; color:var(--ap-primary);'>🎯 <strong>Interest connection:</strong> {interest_note}</div>" if interest_note else ""}
                <hr style='margin:12px 0; border-color:var(--ap-border);'>
                <strong>📝 Instructions:</strong>
                <pre style='font-family:DM Sans,sans-serif; white-space:pre-wrap;
                            color:var(--ap-text); margin-top:8px;'>{act.get('instructions','')}</pre>
                <hr style='margin:12px 0; border-color:var(--ap-border);'>
                <strong>🛒 Supplies:</strong> {act.get('supplies','')}
                <br><br><strong>💡 Expert Tips:</strong> {act.get('tips','')}
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
        st.markdown("### Generate Activities Personalised for a Specific Resident")
        residents = get_residents()
        if not residents:
            st.info("Add residents first to use this feature.")
            return

        liked_activities, disliked_activities = get_activity_ratings_summary()
        resident_map = {r['name']: r for r in residents}
        selected_name = st.selectbox("Select Resident", list(resident_map.keys()))
        resident = resident_map[selected_name]

        st.markdown(f"""
        <div class='ap-card ap-card-sky' style='margin:12px 0;'>
            <strong>{resident['name']}</strong> · Age {resident.get('age','?')} · Room {resident.get('room','?')}<br>
            <span style='color:var(--ap-text-light); font-size:0.85rem;'>
                Mobility: {resident.get('mobility','?')} · Cognitive: {resident.get('cognitive','?')}<br>
                Disabilities: {resident.get('disabilities','None') or 'None'}<br>
                Interests: {resident.get('special_needs','None') or 'None'}
            </span>
        </div>
        """, unsafe_allow_html=True)

        num_activities = st.slider("Number of activities to generate", 1, 5, 3)
        generate_images = st.checkbox("Generate images for each activity 🖼", value=False,
                                      help="Requires OPENAI_API_KEY in secrets.toml.")

        if st.button("🎯 Generate Personalised Activities", type="primary"):
            liked_str = ", ".join(liked_activities[:8]) if liked_activities else "None yet"
            disliked_str = ", ".join(disliked_activities[:8]) if disliked_activities else "None"

            system_prompt = """You are a compassionate expert senior activity director.
Generate activities perfectly suited to an individual resident's abilities, interests, and needs.
Respond ONLY with valid JSON array, no markdown, no extra text."""

            prompt = f"""Generate {num_activities} personalised activities for this resident:

Name: {resident['name']}
Age: {resident.get('age', 'Unknown')}
Mobility: {resident.get('mobility', 'independent')}
Cognitive status: {resident.get('cognitive', 'intact')}
Disabilities: {resident.get('disabilities', 'None')}
Dietary restrictions: {resident.get('dietary', 'None')}
Interests & notes: {resident.get('special_needs', '') + ' ' + resident.get('notes', '')}

Group ratings intelligence:
- Activities residents loved (safe to draw inspiration from): {liked_str}
- Activities that did not engage residents well (avoid): {disliked_str}

Create activities that work WITH their limitations. Make them meaningful and joyful for THIS specific person.

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
    "adaptations": "Specific adaptations made for this resident",
    "image_prompt": "DALL-E prompt for a warm photo of a senior doing this activity"
  }}
]"""

            with st.spinner(f"Crafting personalised activities for {resident['name']}..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    activities = json.loads(clean)
                    st.session_state.personalized_activities = activities
                    st.session_state.personalized_for = resident['name']
                    st.session_state.personalized_generate_images = generate_images
                except Exception:
                    st.error("Could not parse response.")

        if st.session_state.get("personalized_activities"):
            acts = st.session_state.personalized_activities
            want_images = st.session_state.get("personalized_generate_images", False)
            st.markdown(f"### 🎯 Activities for {st.session_state.get('personalized_for','')}")

            for i, act in enumerate(acts):
                with st.expander(
                    f"**{act['title']}** — {act.get('category','').title()} · {act.get('duration_minutes',30)} min"
                ):
                    if want_images:
                        with st.spinner("🖼 Generating image..."):
                            img_url = generate_activity_image(
                                act['title'], act.get('category', ''), act.get('description', '')
                            )
                        if img_url:
                            st.image(img_url, use_container_width=True)

                    st.markdown(f"""
                    <div class='ap-card ap-card-lavender'>
                        <div style='background:var(--ap-primary-light); border-radius:8px; padding:10px;
                                    margin-bottom:12px; border-left:3px solid var(--ap-primary);'>
                            <strong style='color:var(--ap-primary);'>💚 Why this works:</strong>
                            {act.get('why_this_works','')}
                        </div>
                        <p>{act.get('description','')}</p>
                        <strong>Instructions:</strong>
                        <pre style='font-family:DM Sans,sans-serif; white-space:pre-wrap;
                                    color:var(--ap-text);'>{act.get('instructions','')}</pre>
                        <strong>Supplies:</strong> {act.get('supplies','')}
                        <br><strong>Adaptations:</strong> {act.get('adaptations','')}
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"💾 Save Activity #{i+1}", key=f"save_personal_{i}"):
                        act['is_special_needs'] = 0
                        save_activity(act)
                        st.success(f"Saved '{act['title']}'!")
