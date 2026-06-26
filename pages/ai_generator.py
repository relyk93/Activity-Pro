import streamlit as st
import json
import requests
import calendar as cal_module
from utils.auth import require_pro
from utils.database import (get_residents, save_activity, save_event,
                             get_activities, get_activity_ratings_summary,
                             get_resident_interests)
from datetime import date, timedelta

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

FOCUS_AREAS = [
    "Physical", "Mindful", "Social", "Cognitive", "Creative",
    "Photo & Memory", "Music & Movement", "Sensory Stimulation",
    "Spiritual / Reflective", "Nature & Outdoors", "Culinary",
    "Intergenerational", "Life Skills", "Reminiscence Therapy",
    "Pet Therapy", "Art Therapy", "Trivia & Education", "Aromatherapy",
]

PRESET_INTERESTS = [
    "Music & Singing", "Gardening & Plants", "Reading & Books",
    "Crafts & Art", "Cooking & Baking", "Dancing",
    "Movies & TV", "Sports & Games", "Cards & Board Games",
    "Photography", "Nature & Birdwatching", "Animals & Pets",
    "Puzzles & Brain Games", "Poetry & Writing", "Religion & Spirituality",
    "History & Reminiscing", "Family & Grandchildren", "Travel Memories",
    "Exercise & Stretching", "Painting & Drawing", "Flower Arranging",
    "Knitting & Sewing", "Technology & Video Calls", "Storytelling",
    "Trivia & Quiz Games", "Bingo", "Current Events & News",
    "Letter Writing", "Jewelry Making", "Woodworking & Carving",
    "Manicures & Beauty", "Volunteering & Helping Others",
]

FACILITY_REQUIREMENTS = [
    ("exercise_daily",           "Exercise / Physical Activity",  "daily — every active day"),
    ("mens_group_weekly",        "Men's Group",                   "weekly (at least once)"),
    ("spiritual_weekly",         "Spiritual Activity",            "2–3× per week"),
    ("outing_weekly",            "Community Outing",              "weekly (at least once)"),
    ("therapeutic_art_weekly",   "Therapeutic Art",               "2–3× per week"),
    ("therapeutic_music_weekly", "Therapeutic Music",             "2–3× per week"),
    ("aromatherapy_weekly",      "Aromatherapy (include cooking)", "weekly (at least once)"),
    ("family_night_monthly",     "Family Night",                  "monthly"),
    ("health_info_monthly",      "Health Information Activity",   "monthly"),
    ("science_monthly",          "Science Activity",              "2–3× per month"),
    ("animal_monthly",           "Animal / Pet Activity",         "2–3× per month"),
    ("resident_council_monthly", "Resident Council Meeting",      "monthly (mandatory)"),
    ("food_chat_monthly",        "Food Chat / Nutrition Talk",    "1st Wednesday of month, 10:00 AM"),
    ("town_hall_monthly",        "Town Hall Meeting",             "monthly (week 4)"),
    ("bingo_weekly",             "Bingo",                        "weekly — see frequency below"),
    ("discussions_dawn_thursday","Discussions with Dawn",        "every Thursday 11:00 AM — Activities Room"),
]

# Which week number(s) within a month each monthly requirement gets scheduled
_MONTHLY_WEEK_SCHEDULE = {
    "resident_council_monthly": {4},
    "health_info_monthly":      {2},
    "family_night_monthly":     {3},
    "science_monthly":          {1, 3},
    "animal_monthly":           {2, 4},
    "food_chat_monthly":        {1},
    "town_hall_monthly":        {4},
}


def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta + 7 * (n - 1))

def _last_weekday(year, month, weekday):
    import calendar as _c
    last = date(year, month, _c.monthrange(year, month)[1])
    delta = (last.weekday() - weekday) % 7
    return last - timedelta(days=delta)

def _us_holidays(year):
    """Return {date: holiday_name} for major US holidays and seasonal events."""
    h = {
        date(year, 1, 1):  "New Year's Day",
        date(year, 2, 14): "Valentine's Day",
        date(year, 3, 17): "St. Patrick's Day",
        date(year, 7, 4):  "Independence Day / 4th of July",
        date(year, 10, 31):"Halloween",
        date(year, 11, 11):"Veterans Day",
        date(year, 12, 24):"Christmas Eve",
        date(year, 12, 25):"Christmas Day",
        date(year, 12, 31):"New Year's Eve",
        date(year, 3, 20): "First Day of Spring",
        date(year, 6, 21): "First Day of Summer",
        date(year, 9, 22): "First Day of Fall / Autumn",
        date(year, 12, 21):"First Day of Winter",
        _nth_weekday(year, 1, 0, 3):  "Martin Luther King Jr. Day",
        _nth_weekday(year, 2, 0, 3):  "Presidents' Day",
        _nth_weekday(year, 5, 6, 2):  "Mother's Day",
        _last_weekday(year, 5, 0):    "Memorial Day",
        _nth_weekday(year, 6, 6, 3):  "Father's Day",
        _nth_weekday(year, 9, 0, 1):  "Labor Day",
        _nth_weekday(year, 10, 0, 2): "Columbus Day",
        _nth_weekday(year, 11, 3, 4): "Thanksgiving",
    }
    return h

def _parse_time_hour(t):
    """Convert '8:00 AM' / '12:00 PM' string to 24-hour integer."""
    from datetime import datetime as _dt
    return _dt.strptime(t, "%I:%M %p").hour

def _hour_label(h):
    """Convert 24-hour int to '10:00 AM' style string."""
    if h == 0:   return "12:00 AM"
    if h == 12:  return "12:00 PM"
    if h < 12:   return f"{h}:00 AM"
    return f"{h - 12}:00 PM"


def call_claude(prompt, system_prompt, max_tokens=4000):
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        st.error("Missing ANTHROPIC_API_KEY in .streamlit/secrets.toml")
        return None

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        resp = requests.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=120)
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
    from_profiles = set(all_interests)
    for r in residents:
        if r.get('special_needs'):
            for i in r['special_needs'].split(','):
                i = i.strip()
                if i:
                    from_profiles.add(i.title())

    profile_list = sorted(from_profiles)
    all_options  = sorted(from_profiles | set(PRESET_INTERESTS))
    default      = profile_list[:min(8, len(profile_list))] if profile_list else PRESET_INTERESTS[:6]

    st.markdown("**Resident Interest Pool**")
    st.caption("Profile interests selected by default. Add any from the full list to expand the week's theme.")
    selected = st.multiselect(
        "Focus on these interests",
        options=all_options,
        default=default,
        key="interest_pool",
    )
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

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📅 Generate Weekly Calendar", "✨ Generate Single Activity",
         "🔧 Customize for Residents", "📖 Story Generator"]
    )

    # ─── Tab 1: Weekly / Monthly Calendar ───
    with tab1:
        st.markdown("### Generate Activity Calendar")

        with st.expander("🏥 Facility Settings", expanded=False):
            fc1, fc2 = st.columns(2)
            with fc1:
                st.text_input(
                    "Facility Name",
                    key="facility_name",
                    placeholder="e.g. Sunrise Senior Living",
                )
            with fc2:
                st.text_input(
                    "Program Name",
                    key="program_name",
                    placeholder="e.g. Enrichment Activities Program",
                )
            st.markdown("**Meal Times** — activities are scheduled around these")
            _MEAL_OPTS = [
                "6:00 AM","6:30 AM","7:00 AM","7:30 AM","8:00 AM","8:30 AM","9:00 AM",
                "11:00 AM","11:30 AM","12:00 PM","12:30 PM","1:00 PM",
                "4:00 PM","4:30 PM","5:00 PM","5:30 PM","6:00 PM","6:30 PM",
            ]
            mt1, mt2, mt3 = st.columns(3)
            with mt1:
                st.selectbox("Breakfast", _MEAL_OPTS,
                             index=_MEAL_OPTS.index("8:00 AM"), key="meal_breakfast")
            with mt2:
                st.selectbox("Lunch", _MEAL_OPTS,
                             index=_MEAL_OPTS.index("12:00 PM"), key="meal_lunch")
            with mt3:
                st.selectbox("Dinner / Wind-down", _MEAL_OPTS,
                             index=_MEAL_OPTS.index("5:00 PM"), key="meal_dinner")

        residents = get_residents()
        liked_activities, disliked_activities = get_activity_ratings_summary()
        all_disabilities = set()
        for r in residents:
            if r.get('disabilities'):
                for d in r['disabilities'].split(','):
                    d = d.strip()
                    if d:
                        all_disabilities.add(d)

        # ── Mode selector ──
        gen_mode = st.radio(
            "Generate for",
            ["📅 Week (7 days)", "🗓 Month (28–31 days)"],
            horizontal=True,
        )
        is_monthly = "Month" in gen_mode

        col1, col2 = st.columns(2)
        with col1:
            if is_monthly:
                mc1, mc2 = st.columns(2)
                with mc1:
                    sel_month = st.selectbox(
                        "Month",
                        range(1, 13),
                        index=date.today().month - 1,
                        format_func=lambda m: date(2000, m, 1).strftime("%B"),
                    )
                with mc2:
                    sel_year = st.selectbox(
                        "Year",
                        range(date.today().year, date.today().year + 2),
                    )
                start_date = date(sel_year, sel_month, 1)
            else:
                start_date = st.date_input(
                    "Week Starting",
                    value=date.today() - timedelta(days=date.today().weekday()),
                )

            daily_count = st.slider(
                "Active activities per day",
                3, 5, 5,
                help="A 6th Movie Matinee is always added automatically.",
            )
            st.caption("🎬 6th activity: Movie Matinee — AI generates a genre each day")
            include_special = st.checkbox("Include special needs group activities", value=True)
            special_occasions = st.text_area(
                "Special events & occasions" if is_monthly else "Special events this week?",
                placeholder="e.g. Father's Day BBQ 6/17, Medford Cruise 6/20, Margaret's birthday",
                height=80,
            )

            st.caption("Days to generate activities for")
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_cols = st.columns(7)
            active_days = []
            for i, day_name in enumerate(days_of_week):
                default_checked = day_name not in ("Saturday", "Sunday")
                if day_cols[i].checkbox(day_name[:3], value=default_checked, key=f"day_sel_{day_name}"):
                    active_days.append(day_name)

        with col2:
            focus_areas = st.multiselect(
                "Focus areas",
                FOCUS_AREAS,
                default=["Physical", "Mindful", "Social"],
            )
            budget_options = st.multiselect(
                "Weekly budget (select all that apply)",
                ["Free / No Cost", "Under $20", "Under $50", "No limit"],
                default=["Free / No Cost", "Under $20"],
            )
            budget = " and ".join(budget_options) if budget_options else "No limit"
            allow_repeats = st.checkbox(
                "Allow repeating highly-rated activities",
                value=True,
                help="Activities your residents rated 3.5★+ can be suggested again.",
            )

        # Interests panel
        selected_interests = _interests_section(residents)

        # Facility compliance requirements
        with st.expander("📋 Facility Compliance Requirements", expanded=False):
            st.caption(
                "Requirements your facility must meet. Checked items are scheduled first — "
                "the AI fills remaining slots with general programming."
            )
            if "outing_location" not in st.session_state:
                st.session_state["outing_location"] = "McMinnville, Oregon and surrounding area"
            st.text_input(
                "Outing location",
                key="outing_location",
                placeholder="e.g. McMinnville, Oregon",
            )
            st.markdown("**Requirements to enforce:**")
            req_c1, req_c2 = st.columns(2)
            for ri, (req_key, req_label, req_freq) in enumerate(FACILITY_REQUIREMENTS):
                label = f"{req_label} ({req_freq})" if req_key != "bingo_weekly" else "Bingo"
                target_col = req_c1 if ri % 2 == 0 else req_c2
                target_col.checkbox(label, value=True, key=f"req_{req_key}")

            if st.session_state.get("req_bingo_weekly", True):
                bc1, bc2 = st.columns(2)
                with bc1:
                    st.selectbox(
                        "Bingo — days per week",
                        ["1 day / week", "2 days / week", "3 days / week"],
                        index=1,
                        key="bingo_freq",
                    )
                with bc2:
                    st.caption("Preferred time: **2:00 PM**")

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

        btn_label = "🗓 Generate Monthly Calendar" if is_monthly else "🤖 Generate Weekly Calendar"
        if not active_days:
            st.warning("Select at least one day above before generating.")
        if st.button(btn_label, type="primary", use_container_width=True, disabled=not active_days):
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

            # Compute activity time slots from meal settings
            breakfast_t = st.session_state.get("meal_breakfast", "8:00 AM")
            lunch_t     = st.session_state.get("meal_lunch",     "12:00 PM")
            dinner_t    = st.session_state.get("meal_dinner",    "5:00 PM")
            lunch_h  = _parse_time_hour(lunch_t)
            dinner_h = _parse_time_hour(dinner_t)
            # Slots: pre-lunch, then post-lunch up to pre-dinner
            raw_slots = [lunch_h - 1] + [lunch_h + i for i in range(1, dinner_h - lunch_h)]
            raw_slots = sorted(set(h for h in raw_slots if 8 <= h < dinner_h))[:5]
            activity_times = [_hour_label(h) for h in raw_slots]
            windown_time   = dinner_t

            # Build facility requirements for prompt injection
            outing_loc = st.session_state.get("outing_location", "McMinnville, Oregon and surrounding area")
            weekly_req_lines = []
            monthly_reqs_active = {}
            thursday_reqs_active = {}
            for req_key, req_label, req_freq in FACILITY_REQUIREMENTS:
                if st.session_state.get(f"req_{req_key}", True):
                    if req_key.endswith("_monthly"):
                        monthly_reqs_active[req_key] = (req_label, req_freq)
                    elif req_key.endswith("_thursday"):
                        thursday_reqs_active[req_key] = (req_label, req_freq)
                    elif req_key == "bingo_weekly":
                        bingo_freq = st.session_state.get("bingo_freq", "2 days / week")
                        weekly_req_lines.append(
                            f"  - Bingo: {bingo_freq}, preferred time 2:00 PM"
                        )
                    elif req_key == "outing_weekly":
                        weekly_req_lines.append(
                            f"  - {req_label}: {req_freq} (location: {outing_loc})"
                        )
                    else:
                        weekly_req_lines.append(f"  - {req_label}: {req_freq}")

            system_prompt = """You are an expert senior activity director with 20+ years of experience.
You create engaging, therapeutic, joyful activities for seniors aged 60+.
You understand dementia care, mobility limitations, sensory impairments, and emotional wellbeing.
Design activities that are safe, low-cost, emotionally meaningful, dignity-preserving, and evidence-based.
Always spread categories across the day: physical/active early, cognitive/social mid-day, creative/therapeutic afternoon.
The final activity each day MUST be Movie Matinee — a different genre each day chosen to match the week theme.
Respond ONLY with valid JSON, no markdown, no extra text."""

            active_days_set = set(active_days)

            def _build_week_prompt(week_start_d, week_label="", week_num=1):
                # Compute exact dates within this 7-day window that match selected days
                selected_dates = []
                for offset in range(7):
                    d = week_start_d + timedelta(days=offset)
                    if d.strftime("%A") in active_days_set:
                        selected_dates.append(d)

                if not selected_dates:
                    return None

                dates_str = "\n".join(
                    f"  - {d.strftime('%A')} {d.isoformat()}" for d in selected_dates
                )

                # Assemble requirements section for this specific week
                req_lines = list(weekly_req_lines)
                for req_key, (req_label, req_freq) in monthly_reqs_active.items():
                    scheduled_weeks = _MONTHLY_WEEK_SCHEDULE.get(req_key, {1})
                    if week_num in scheduled_weeks:
                        req_lines.append(
                            f"  - {req_label}: include this week ({req_freq})"
                        )
                # Thursday-specific requirements (Farmers Market etc.)
                has_thursday = any(d.strftime("%A") == "Thursday" for d in selected_dates)
                if has_thursday:
                    for req_key, (req_label, req_freq) in thursday_reqs_active.items():
                        req_lines.append(f"  - {req_label}: {req_freq} — schedule on Thursday")

                req_section = ""
                if req_lines:
                    req_section = (
                        "\nMANDATORY FACILITY REQUIREMENTS — schedule these FIRST, "
                        "then fill remaining slots with varied programming:\n"
                        + "\n".join(req_lines)
                        + "\n"
                    )

                # Holiday / observance detection
                year = selected_dates[0].year
                holidays_map = _us_holidays(year)
                week_holidays = {
                    d: name for d, name in holidays_map.items()
                    if d in set(selected_dates)
                }
                holiday_section = ""
                if week_holidays:
                    hlines = "\n".join(
                        f"  - {d.strftime('%A %B %d')}: {name}"
                        for d, name in sorted(week_holidays.items())
                    )
                    holiday_section = (
                        "\nHOLIDAYS / OBSERVANCES THIS PERIOD — "
                        "create at least one themed activity for each:\n"
                        + hlines + "\n"
                    )

                times_str = ", ".join(activity_times[:daily_count]) if activity_times else "11:00 AM, 1:00 PM, 2:00 PM, 3:00 PM, 4:00 PM"

                return f"""Create a {daily_count + 1}-activity-per-day activity calendar for a senior living facility.

Resident profile: {resident_summary}
Resident interests: {interests_str}
Focus areas: {', '.join(focus_areas)}
Budget: {budget}
Meals: Breakfast {breakfast_t} · Lunch {lunch_t} · Dinner {dinner_t}
Special events: {special_occasions if special_occasions else 'None'}
Include special needs activities: {include_special}
{f'({week_label})' if week_label else ''}
{req_section}{holiday_section}
GENERATE ONLY FOR THESE SPECIFIC DATES — no other days:
{dates_str}

ACTIVITY STRUCTURE — follow exactly for each day:
- ALL activities are exactly 60 minutes (facility standard). Set duration_minutes to 60 for every activity.
- Schedule the {daily_count} active activities at these exact times: {times_str}
- Activity {daily_count + 1} (LAST): ALWAYS "Movie Matinee" at {windown_time}.
  Pick a different senior-friendly movie genre each day that fits the week theme (e.g. Classic Western,
  Musical, Comedy, Romance, Nature Documentary, Holiday Film, Drama, Adventure).
  Use title "Movie Matinee: [Genre]" (e.g. "Movie Matinee: Classic Western"),
  category "social", time "{windown_time}", duration_minutes 60, cost "Free",
  supplies "Projector or large-screen TV, popcorn, comfortable seating", group_type "all".
  Description: name the genre and give one sentence on why residents will enjoy it. Vary genre every day.

RATINGS INTELLIGENCE:
- Residents loved (safe to reuse if allowed): {liked_str}
- Avoid or rethink: {disliked_str}
- {repeat_instruction}
- Don't duplicate: {', '.join(existing_titles[:20])}

Return a JSON object. Keep description to one sentence — brevity is required to fit output limits:
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
          "duration_minutes": 60,
          "cost_estimate": "Free",
          "description": "One sentence.",
          "supplies": "Item 1, Item 2",
          "location": "Activity Room"
        }}
      ]
    }}
  ]
}}"""

            if is_monthly:
                # Build list of week start dates covering the full month
                days_in_month = cal_module.monthrange(start_date.year, start_date.month)[1]
                month_end = start_date + timedelta(days=days_in_month - 1)
                week_starts = []
                d = start_date
                while d <= month_end:
                    week_starts.append(d)
                    d += timedelta(days=7)

                all_days = []
                month_theme = f"{start_date.strftime('%B %Y')} Calendar"
                progress = st.progress(0, text="Starting monthly generation...")

                for wi, ws in enumerate(week_starts):
                    # Clip last week to not exceed month end
                    week_label = f"(Week {wi + 1} of {len(week_starts)})"
                    progress.progress(
                        int(wi / len(week_starts) * 100),
                        text=f"Generating {week_label}…",
                    )
                    week_prompt = _build_week_prompt(ws, week_label, week_num=wi + 1)
                    if not week_prompt:
                        continue  # no selected days fall in this week chunk
                    res = call_claude(week_prompt, system_prompt, max_tokens=8000)
                    if res:
                        try:
                            clean = res.strip().replace("```json", "").replace("```", "").strip()
                            week_data = json.loads(clean)
                            # Only keep days within the actual month
                            for day in week_data.get("days", []):
                                try:
                                    day_d = date.fromisoformat(day["date"])
                                    if start_date <= day_d <= month_end:
                                        all_days.append(day)
                                except Exception:
                                    all_days.append(day)
                            if wi == 0:
                                month_theme = week_data.get("week_theme", month_theme)
                        except Exception as e:
                            st.warning(f"Week {wi + 1} ({ws}) parse error — skipped. Try reducing active activities per day or selected days. ({e})")
                    else:
                        st.warning(f"Week {wi + 1} generation failed — skipped.")

                progress.progress(100, text="Done!")
                if all_days:
                    calendar_data = {"week_theme": month_theme, "days": all_days}
                    st.session_state.generated_calendar = calendar_data
                    st.success(f"✅ Generated **{len(all_days)} days** for {start_date.strftime('%B %Y')}: **{month_theme}**")
                else:
                    st.error("Monthly generation failed. Check your API key and try again.")
            else:
                week_prompt = _build_week_prompt(start_date)
                if not week_prompt:
                    st.error("None of the selected days fall within the chosen week. Adjust your day selection or start date.")
                    st.stop()
                with st.spinner("🌸 Crafting your personalised week…"):
                    result = call_claude(week_prompt, system_prompt, max_tokens=8000)

                if result:
                    try:
                        clean = result.strip().replace("```json", "").replace("```", "").strip()
                        calendar_data = json.loads(clean)
                        st.session_state.generated_calendar = calendar_data
                        st.success(f"✅ Generated: **{calendar_data.get('week_theme', 'Weekly Activities')}**")
                    except Exception as e:
                        st.error(f"Could not parse AI response. Please try again. ({e})")
                else:
                    st.error("API call failed. Please check your connection.")

        # ── Preview & selective save ──
        if st.session_state.get("generated_calendar"):
            cal = st.session_state.generated_calendar

            # Build a flat list of all activities with their day context
            all_acts = []
            for day in cal.get("days", []):
                for act in day.get("activities", []):
                    all_acts.append({"day": day["day_name"], "date": day["date"], "act": act})

            total = len(all_acts)
            st.markdown(f"### 🗓 {cal.get('week_theme', 'Weekly Calendar')} — {total} activities generated")

            # Select-all / none controls
            ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 4])
            with ctrl_col1:
                if st.button("☑ Select All", use_container_width=True):
                    for i in range(total):
                        st.session_state[f"cal_sel_{i}"] = True
                    st.rerun()
            with ctrl_col2:
                if st.button("☐ Select None", use_container_width=True):
                    for i in range(total):
                        st.session_state[f"cal_sel_{i}"] = False
                    st.rerun()

            # Initialise checkboxes to True on first render
            for i in range(total):
                if f"cal_sel_{i}" not in st.session_state:
                    st.session_state[f"cal_sel_{i}"] = True

            # Group by day for display
            days_seen = {}
            for idx, item in enumerate(all_acts):
                day_key = item["date"]
                if day_key not in days_seen:
                    days_seen[day_key] = []
                days_seen[day_key].append((idx, item))

            for day_date, items in days_seen.items():
                day_name = items[0][1]["day"]
                selected_in_day = sum(1 for i, _ in items if st.session_state.get(f"cal_sel_{i}", True))
                with st.expander(
                    f"**{day_name} · {day_date}** — {selected_in_day}/{len(items)} selected",
                    expanded=True,
                ):
                    for idx, item in items:
                        act = item["act"]
                        cat = act.get("category", "social")
                        is_special = act.get("group_type") == "special_needs"
                        interest_note = act.get("interest_connection", "")

                        cb_col, card_col = st.columns([0.07, 0.93])
                        with cb_col:
                            st.session_state[f"cal_sel_{idx}"] = st.checkbox(
                                "",
                                value=st.session_state.get(f"cal_sel_{idx}", True),
                                key=f"cb_{idx}",
                                label_visibility="collapsed",
                            )
                        with card_col:
                            opacity = "1" if st.session_state.get(f"cal_sel_{idx}", True) else "0.4"
                            st.markdown(f"""
                            <div class='ap-card {"ap-card-lavender" if is_special else "ap-card-sage"}'
                                 style='margin-bottom:8px; opacity:{opacity}; transition:opacity 0.2s;'>
                                <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                                    <div>
                                        <strong>{'🟣 ' if is_special else ''}{act['title']}</strong>
                                        <div style='color:var(--ap-text-light); font-size:0.82rem; margin-top:2px;'>
                                            🕐 {act.get('time','TBD')} · ⏱ {act.get('duration_minutes',60)} min ·
                                            💰 {act.get('cost_estimate','Free')} · 📍 {act.get('location','Activity Room')}
                                        </div>
                                        <div style='margin-top:5px; font-size:0.88rem; color:var(--ap-text-mid);'>
                                            {act.get('description','')}
                                        </div>
                                        {f"<div style='margin-top:4px; font-size:0.8rem; color:var(--ap-primary);'>🎯 {interest_note}</div>" if interest_note else ""}
                                    </div>
                                    <span class='tag tag-{cat}'>{cat.title()}</span>
                                </div>
                                <div style='margin-top:8px; font-size:0.82rem;'>
                                    <strong style='color:var(--ap-text-light);'>SUPPLIES:</strong>
                                    {act.get('supplies','None needed')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            # Count selected
            selected_indices = [i for i in range(total) if st.session_state.get(f"cal_sel_{i}", True)]
            selected_count = len(selected_indices)

            st.markdown(f"**{selected_count} of {total} activities selected**")

            save_col, discard_col = st.columns(2)
            with save_col:
                btn_label = f"💾 Add {selected_count} Selected to Calendar"
                if st.button(btn_label, type="primary", use_container_width=True, disabled=selected_count == 0):
                    saved = 0
                    for i in selected_indices:
                        item = all_acts[i]
                        act = item["act"]
                        act_id = save_activity({
                            "title": act["title"],
                            "description": act.get("description", ""),
                            "instructions": act.get("instructions", ""),
                            "supplies": act.get("supplies", ""),
                            "category": act.get("category", "social"),
                            "duration_minutes": act.get("duration_minutes", 60),
                            "cost_estimate": act.get("cost_estimate", "Free"),
                            "difficulty": "easy",
                            "group_type": act.get("group_type", "all"),
                            "disability_friendly": act.get("disability_friendly", ""),
                            "is_special_needs": 1 if act.get("group_type") == "special_needs" else 0,
                            "created_by": "AI",
                        })
                        save_event({
                            "activity_id": act_id,
                            "title": act["title"],
                            "date": item["date"],
                            "time": act.get("time", "10:00 AM"),
                            "location": act.get("location", "Activity Room"),
                            "group_type": act.get("group_type", "all"),
                            "notes": "",
                        })
                        saved += 1
                    # Clear checkboxes
                    for i in range(total):
                        st.session_state.pop(f"cal_sel_{i}", None)
                    st.session_state.generated_calendar = None
                    st.success(f"✅ {saved} activities added to your calendar!")
                    st.rerun()
            with discard_col:
                if st.button("🗑 Discard All", use_container_width=True):
                    for i in range(total):
                        st.session_state.pop(f"cal_sel_{i}", None)
                    st.session_state.generated_calendar = None
                    st.rerun()

            # ── Supply List Export ──
            st.markdown("---")
            st.markdown("### 🛒 Supply List")

            skip = {"none", "none needed", "nothing", "n/a", ""}
            by_day_supply = []
            consolidated = {}
            for day in cal.get("days", []):
                day_acts = []
                for act in day.get("activities", []):
                    items = [
                        s.strip() for s in (act.get("supplies") or "").split(",")
                        if s.strip().lower() not in skip
                    ]
                    if items:
                        day_acts.append({"title": act["title"], "supplies": items})
                        for item in items:
                            key = item.lower()
                            if key not in consolidated:
                                consolidated[key] = {"display": item, "activities": []}
                            consolidated[key]["activities"].append(act["title"])
                if day_acts:
                    by_day_supply.append({
                        "date": day["date"],
                        "day_name": day.get("day_name", ""),
                        "activities": day_acts,
                    })

            if not by_day_supply:
                st.caption("No supplies needed for any of the generated activities.")
            else:
                st.caption(f"{len(consolidated)} unique supply items across {len(by_day_supply)} days")

                sup_tab1, sup_tab2 = st.tabs(["📅 By Day", "🗒 Shopping List"])
                with sup_tab1:
                    for day in by_day_supply:
                        label = f"{day['day_name']} {day['date']}" if day.get('day_name') else day['date']
                        with st.expander(label, expanded=False):
                            for act in day["activities"]:
                                st.markdown(f"**{act['title']}**")
                                for s in act["supplies"]:
                                    st.markdown(f"- {s}")
                with sup_tab2:
                    st.caption("Alphabetical — deduplicated across all activities")
                    for key in sorted(consolidated):
                        v = consolidated[key]
                        acts_str = " · ".join(sorted(set(v["activities"])))
                        st.markdown(f"**{v['display']}** — _{acts_str}_")

                # Build download content
                period_label = cal.get("week_theme", "Generated Calendar")
                csv_rows = [f"Supply List — {period_label}", "Date,Day,Activity,Supply Item"]
                for day in by_day_supply:
                    for act in day["activities"]:
                        for s in act["supplies"]:
                            csv_rows.append(f"{day['date']},{day.get('day_name','')},{act['title']},{s}")
                csv_data = "\n".join(csv_rows)

                consol_html = "<ul>"
                for key in sorted(consolidated):
                    v = consolidated[key]
                    acts_str = ", ".join(sorted(set(v["activities"])))
                    consol_html += f"<li><strong>{v['display']}</strong> — for: {acts_str}</li>"
                consol_html += "</ul>"
                days_html = ""
                for day in by_day_supply:
                    label = f"{day.get('day_name','')} {day['date']}"
                    days_html += f"<h3 style='color:#0F766E;'>{label}</h3><ul>"
                    for act in day["activities"]:
                        days_html += f"<li><strong>{act['title']}</strong>: {', '.join(act['supplies'])}</li>"
                    days_html += "</ul>"
                html_data = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>body{{font-family:Georgia,serif;max-width:700px;margin:40px auto;padding:40px;color:#1A2332;background:#FFFDF9;}}
h1{{color:#0F766E;}}h2{{color:#2D6A4F;border-bottom:1px solid #ccc;padding-bottom:6px;}}
h3{{color:#0F766E;}}ul{{line-height:2;}}
.footer{{margin-top:48px;color:#94A3B8;font-size:0.78rem;text-align:center;}}
@media print{{body{{margin:0;padding:20px;}}}}</style></head><body>
<h1>🛒 Supply List</h1><p style='color:#718096;'>{period_label}</p>
<h2>By Day</h2>{days_html}<h2>Consolidated Shopping List</h2>{consol_html}
<div class='footer'>Generated by ActivityPro</div></body></html>"""

                fname = period_label.replace(" ", "_")[:40]
                dl1, dl2 = st.columns(2)
                with dl1:
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_data,
                        file_name=f"supplies_{fname}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with dl2:
                    st.download_button(
                        "🖨 Download / Print",
                        data=html_data,
                        file_name=f"supplies_{fname}.html",
                        mime="text/html",
                        use_container_width=True,
                        help="Open in browser → File → Print → Save as PDF",
                    )

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
                FOCUS_AREAS,
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
                options=sorted(set(all_interests) | set(PRESET_INTERESTS)),
                default=all_interests[:3] if all_interests else PRESET_INTERESTS[:3],
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

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 Save to Library", type="primary", use_container_width=True):
                    save_activity(act)
                    st.success(f"✅ '{act['title']}' saved to your activity library!")
                    st.session_state.single_activity = None
            with c2:
                if st.button("📅 Add to Calendar", use_container_width=True):
                    st.session_state.single_add_to_cal = True
            with c3:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.single_activity = None
                    st.session_state.pop("single_add_to_cal", None)
                    st.rerun()

            if st.session_state.get("single_add_to_cal"):
                st.markdown("---")
                st.markdown("**Schedule this activity**")
                cal_col1, cal_col2, cal_col3 = st.columns(3)
                with cal_col1:
                    event_date = st.date_input("Date", value=date.today(), key="single_event_date")
                with cal_col2:
                    event_time = st.time_input("Time", value=None, key="single_event_time")
                with cal_col3:
                    event_location = st.text_input("Location", value="Activity Room", key="single_event_loc")

                if st.button("✅ Confirm & Add to Calendar", type="primary", use_container_width=True):
                    act_id = save_activity({
                        "title": act["title"],
                        "description": act.get("description", ""),
                        "instructions": act.get("instructions", ""),
                        "supplies": act.get("supplies", ""),
                        "category": act.get("category", "social"),
                        "duration_minutes": act.get("duration_minutes", 60),
                        "cost_estimate": act.get("cost_estimate", "Free"),
                        "difficulty": "easy",
                        "group_type": act.get("group_type", "all"),
                        "disability_friendly": act.get("disability_friendly", ""),
                        "is_special_needs": 0,
                        "created_by": "AI",
                    })
                    time_str = event_time.strftime("%I:%M %p") if event_time else "10:00 AM"
                    save_event({
                        "activity_id": act_id,
                        "title": act["title"],
                        "date": event_date.isoformat(),
                        "time": time_str,
                        "location": event_location,
                        "group_type": act.get("group_type", "all"),
                        "notes": "",
                    })
                    st.success(f"✅ '{act['title']}' added to calendar on {event_date}!")
                    st.session_state.single_activity = None
                    st.session_state.pop("single_add_to_cal", None)
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

    # ─── Tab 4: Story Generator ───
    with tab4:
        st.markdown("### 📖 Personalised Story Generator")
        st.markdown(
            "<div style='color:var(--ap-text-light); margin-bottom:20px;'>"
            "Generate a warm, meaningful story tailored to a resident's life and interests. "
            "Read aloud as a group activity, print as a keepsake, or use as a reminiscence prompt. "
            "Text costs pennies — illustration is optional at ~$0.04/image."
            "</div>",
            unsafe_allow_html=True,
        )

        residents = get_residents()

        col1, col2 = st.columns(2)
        with col1:
            story_for = st.selectbox(
                "Story for",
                ["Whole Group"] + [r["name"] for r in residents],
                key="story_for",
            )
            story_type = st.selectbox(
                "Story type",
                [
                    "Reminiscence / Life Story",
                    "Adventure & Nature",
                    "Fairy Tale / Fable",
                    "Historical Fiction",
                    "Holiday & Seasonal",
                    "Inspirational / Uplifting",
                    "Animal Story",
                    "Mystery & Gentle Suspense",
                    "Group Chain Story (collaborative prompt)",
                ],
                key="story_type",
            )
            story_length = st.select_slider(
                "Length",
                ["Short (~1 page)", "Medium (~2 pages)", "Long (~4 pages)"],
                value="Medium (~2 pages)",
                key="story_length",
            )

        with col2:
            theme_setting = st.text_input(
                "Theme or setting (optional)",
                placeholder="e.g. 1950s diner, seaside village, autumn garden",
                key="story_theme",
            )
            reading_level = st.select_slider(
                "Reading level",
                ["Simple & Clear", "Standard", "Rich & Descriptive"],
                value="Standard",
                key="story_reading_level",
            )
            generate_illustration = st.checkbox(
                "Generate cover illustration 🖼",
                value=False,
                key="story_gen_image",
                help="~$0.04 per image via DALL-E 3. Requires OPENAI_API_KEY in secrets.",
            )
            add_discussion = st.checkbox(
                "Add discussion questions",
                value=True,
                key="story_discussion",
                help="Great for group read-aloud sessions",
            )

        special_details = st.text_area(
            "Personal details to weave in (optional)",
            placeholder=(
                "e.g. Margaret grew up near the sea, her late husband was a fisherman, "
                "she loves roses and used to bake apple pie every Sunday."
            ),
            key="story_details",
            height=90,
        )

        if st.button("✍️ Generate Story", type="primary", use_container_width=True):
            if story_for != "Whole Group":
                r = next((r for r in residents if r["name"] == story_for), None)
                if r:
                    resident_context = (
                        f"Name: {r['name']}, Age {r.get('age','?')}, "
                        f"Mobility: {r.get('mobility','')}, Cognitive: {r.get('cognitive','')}, "
                        f"Interests/Notes: {(r.get('special_needs','') or '') + ' ' + (r.get('notes','') or '')}"
                    )
                else:
                    resident_context = story_for
            else:
                resident_context = f"A group of {len(residents)} seniors aged 60+ with varied backgrounds"

            length_words = {
                "Short (~1 page)":    "300–400 words",
                "Medium (~2 pages)":  "600–800 words",
                "Long (~4 pages)":    "1200–1500 words",
            }[story_length]

            system_prompt = (
                "You are a gifted therapeutic storyteller specialising in stories for seniors. "
                "Your stories are warm, dignified, emotionally resonant, and accessible. "
                "Weave in personal history naturally — never patronising, always uplifting. "
                "Respond ONLY with valid JSON, no markdown fences, no extra text."
            )

            prompt = f"""Write a {story_type} story.

Audience: {resident_context}
Length: {length_words}
Theme/setting: {theme_setting if theme_setting else "your choice, something warm and familiar"}
Reading level: {reading_level}
Personal details to include: {special_details if special_details else "None — use the resident profile above"}
Add discussion questions: {add_discussion}

Make the story feel personal, not generic. If it is a reminiscence story, draw on the resident's era,
interests, and probable memories. The protagonist should feel recognisable and dignified.

Return this exact JSON:
{{
  "title": "Story title",
  "tagline": "One evocative sentence",
  "story": "Full story text. Use \\n\\n between paragraphs.",
  "reflection": "A gentle 1-2 sentence closing thought or moral",
  "discussion_questions": ["Question 1?", "Question 2?", "Question 3?"],
  "illustration_prompt": "A detailed, warm DALL-E 3 prompt for a cover illustration. No text in image."
}}"""

            with st.spinner("✍️ Crafting your story..."):
                result = call_claude(prompt, system_prompt)

            if result:
                try:
                    clean = result.strip().replace("```json", "").replace("```", "").strip()
                    st.session_state.generated_story = json.loads(clean)
                    st.session_state.story_for_display = story_for
                    st.session_state.story_want_image = generate_illustration
                    st.session_state.story_want_discussion = add_discussion
                except Exception as e:
                    st.error(f"Could not parse story response. Try again. ({e})")

        # ── Display generated story ──
        if st.session_state.get("generated_story"):
            story = st.session_state.generated_story
            for_name = st.session_state.get("story_for_display", "")
            want_img  = st.session_state.get("story_want_image", False)
            want_disc = st.session_state.get("story_want_discussion", True)

            st.markdown("---")

            # Optional illustration
            img_url = None
            if want_img:
                with st.spinner("🖼 Generating cover illustration via DALL-E 3..."):
                    img_url = generate_activity_image(
                        story["title"], "storytelling",
                        story.get("illustration_prompt", story.get("tagline", "")),
                    )
                if not img_url:
                    st.caption("Image skipped — add OPENAI_API_KEY to Streamlit secrets to enable.")

            if img_url:
                st.image(img_url, caption=story["title"], use_container_width=True)

            # Story card
            for_line = (
                f"<div style='margin-top:6px; color:var(--ap-primary); font-size:0.85rem;'>"
                f"For {for_name}</div>"
                if for_name and for_name != "Whole Group" else ""
            )
            reflection_html = (
                f"<div style='margin-top:28px; padding-top:18px; border-top:1px solid var(--ap-border); "
                f"color:var(--ap-text-mid); font-style:italic; font-size:0.95rem;'>"
                f"{story['reflection']}</div>"
            ) if story.get("reflection") else ""

            st.markdown(f"""
            <div class='ap-card' style='max-width:720px; margin:0 auto; padding:40px;'>
                <div style='text-align:center; margin-bottom:32px;'>
                    <h1 style='font-family:Playfair Display,serif; font-size:1.8rem;
                               color:var(--ap-text); margin-bottom:6px;'>{story['title']}</h1>
                    <div style='color:var(--ap-text-light); font-style:italic;'>{story.get('tagline','')}</div>
                    {for_line}
                </div>
                <div style='font-size:1rem; line-height:2; color:var(--ap-text);'>
                    {story['story'].replace(chr(10)+chr(10), '<br><br>')}
                </div>
                {reflection_html}
            </div>
            """, unsafe_allow_html=True)

            # Discussion questions
            if want_disc and story.get("discussion_questions"):
                st.markdown("#### 💬 Discussion Questions")
                for i, q in enumerate(story["discussion_questions"], 1):
                    st.markdown(f"**{i}.** {q}")

            # Action buttons
            btn1, btn2, btn3 = st.columns(3)

            with btn1:
                # Build print-ready HTML
                disc_html = ""
                if story.get("discussion_questions"):
                    qs = "".join(
                        f"<li style='margin:8px 0;'>{q}</li>"
                        for q in story["discussion_questions"]
                    )
                    disc_html = (
                        f"<div style='margin-top:40px; padding-top:24px; border-top:2px solid #E2DDD6;'>"
                        f"<h3 style='color:#0F766E;'>💬 Discussion Questions</h3>"
                        f"<ol style='color:#4A5568; line-height:2;'>{qs}</ol></div>"
                    )
                img_tag = (
                    f"<img src='{img_url}' style='width:100%; border-radius:12px; margin-bottom:32px;'>"
                    if img_url else ""
                )
                printable = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{font-family:Georgia,serif; max-width:680px; margin:40px auto; padding:40px;
         color:#1A2332; background:#FFFDF9; line-height:1.9;}}
  h1   {{font-size:2rem; text-align:center; color:#0F766E; margin-bottom:6px;}}
  .tag {{text-align:center; color:#718096; font-style:italic; margin-bottom:32px;}}
  .story {{font-size:1.05rem;}}
  .reflection {{margin-top:32px; padding-top:18px; border-top:1px solid #E2DDD6;
                color:#4A5568; font-style:italic;}}
  .footer {{margin-top:48px; text-align:center; color:#94A3B8; font-size:0.78rem;}}
  @media print {{body {{margin:0; padding:20px;}}}}
</style></head>
<body>
  {img_tag}
  <h1>{story['title']}</h1>
  <div class="tag">{story.get('tagline','')}</div>
  <div class="story">{story['story'].replace(chr(10)+chr(10),'<br><br>')}</div>
  {f'<div class="reflection">{story["reflection"]}</div>' if story.get('reflection') else ''}
  {disc_html}
  <div class="footer">Generated by ActivityPro · {date.today().strftime('%B %d, %Y')}</div>
</body></html>"""

                fname = story["title"].replace(" ", "_")[:40]
                st.download_button(
                    "📄 Download / Print",
                    data=printable,
                    file_name=f"{fname}.html",
                    mime="text/html",
                    use_container_width=True,
                    help="Open in browser → File → Print → Save as PDF",
                )

            with btn2:
                if st.button("💾 Save as Activity", key="save_story_act", use_container_width=True):
                    save_activity({
                        "title": f"Story: {story['title']}",
                        "description": story.get("tagline", ""),
                        "instructions": story["story"][:2000],
                        "supplies": "Printed copies, comfortable seating",
                        "category": "social",
                        "duration_minutes": 30,
                        "cost_estimate": "Free",
                        "difficulty": "easy",
                        "group_type": "all",
                        "disability_friendly": "dementia,hearing_loss,wheelchair",
                        "is_special_needs": 0,
                        "created_by": "AI",
                    })
                    st.success(f"Saved '{story['title']}' to activity library!")

            with btn3:
                if st.button("🔄 New Story", key="new_story", use_container_width=True):
                    st.session_state.generated_story = None
                    st.rerun()
