import streamlit as st
import json
import requests
from utils.database import (get_residents, get_last_activity,
                             get_resident_mood_trend, get_engagements,
                             save_resident)
from utils.database import get_at_risk_residents, get_declining_mood_residents
from datetime import date

MOOD_EMOJI = {1: "😔", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}
MOOD_LABEL = {1: "Very Low", 2: "Low", 3: "Neutral", 4: "Good", 5: "Great"}
MOBILITY_ICON = {
    "independent": ("🟢", "Independent"),
    "cane":        ("🟡", "Uses Cane"),
    "walker":      ("🟡", "Uses Walker"),
    "wheelchair":  ("🔴", "Wheelchair"),
}
COGNITIVE_COLOR = {
    "intact":   "🟢",
    "mild":     "🟡",
    "moderate": "🟠",
    "severe":   "🔴",
}


def _generate_ai_profile(resident: dict) -> dict | None:
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        st.error("ANTHROPIC_API_KEY not configured in Streamlit secrets.")
        return None

    prompt = f"""Generate a realistic sample profile for a senior living facility resident.

Name: {resident.get('name', 'Unknown')}
Age: {resident.get('age', 80)}
Room: {resident.get('room', '?')}

Create a believable, compassionate profile as if this were a real long-term care resident.
Keep disabilities realistic for this age group. Interests should feel personal and specific.
Staff notes should sound like something a care worker would actually write.

Return ONLY valid JSON, no markdown:
{{
  "disabilities": "Comma-separated conditions (e.g. Arthritis, Mild hearing loss)",
  "cognitive": "one of: intact / mild / moderate / severe",
  "dietary": "Dietary needs (e.g. Low sodium, diabetic-friendly) or empty string if none",
  "special_needs": "Comma-separated interests and hobbies (6-8 specific ones)",
  "notes": "2-3 sentences of realistic staff notes about personality, preferences, and care tips"
}}"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=20,
        )
        if resp.status_code == 200:
            text = resp.json()["content"][0]["text"]
            clean = text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
    except Exception as e:
        st.error(f"Profile generation failed: {e}")
    return None


def _days_since(date_str: str) -> int:
    try:
        return (date.today() - date.fromisoformat(date_str)).days
    except Exception:
        return 999


def show():
    st.markdown("# 👤 Resident Quick Cards")
    st.caption(
        "Full at-a-glance profile for any resident — care details, interests, "
        "mood trend, and recent activity history in one place."
    )

    residents = get_residents()

    if not residents:
        st.info("No residents added yet.", icon="👀")
        if st.button("➕ Add Residents", type="primary"):
            st.session_state.page = "Residents"
            st.rerun()
        return

    # ── Resident selector ──
    names = [r["name"] for r in residents]

    if "rc_index" not in st.session_state:
        st.session_state.rc_index = 0
    st.session_state.rc_index = min(st.session_state.rc_index, len(residents) - 1)

    sel_col, prev_col, next_col = st.columns([6, 1, 1])
    with sel_col:
        chosen_name = st.selectbox(
            "Select resident",
            names,
            index=st.session_state.rc_index,
            key="rc_dropdown",
            label_visibility="collapsed",
        )
        st.session_state.rc_index = names.index(chosen_name)
    with prev_col:
        if st.button("◀ Prev", use_container_width=True,
                     disabled=st.session_state.rc_index == 0):
            st.session_state.rc_index -= 1
            st.rerun()
    with next_col:
        if st.button("Next ▶", use_container_width=True,
                     disabled=st.session_state.rc_index == len(residents) - 1):
            st.session_state.rc_index += 1
            st.rerun()

    r = residents[st.session_state.rc_index]

    # ── Fetch data ──
    at_risk_ids   = {x["id"] for x in get_at_risk_residents()}
    declining_ids = {x["id"] for x in get_declining_mood_residents()}
    last          = get_last_activity(r["id"])
    trend         = get_resident_mood_trend(r["id"], limit=8)
    engs          = get_engagements(resident_id=r["id"])

    total_sessions = len(engs)
    engaged_count  = sum(1 for e in engs if e["engaged"])
    eng_rate       = int(engaged_count / total_sessions * 100) if total_sessions else None

    if last:
        days_ago = _days_since(last["event_date"])
        last_label = (
            "Today" if days_ago == 0 else
            "Yesterday" if days_ago == 1 else
            f"{days_ago} days ago"
        )
        last_str = f"{last['event_title']} · {last_label}"
    else:
        last_str = "No activity recorded yet"

    mob_icon, mob_label = MOBILITY_ICON.get(r.get("mobility", "independent"), ("⚪", "Unknown"))
    cog_level = (r.get("cognitive") or "intact").lower()
    cog_icon  = COGNITIVE_COLOR.get(cog_level, "⚪")
    disabilities = [d.strip() for d in (r.get("disabilities") or "").split(",") if d.strip()]
    interests    = [i.strip() for i in (r.get("special_needs") or "").split(",") if i.strip()]

    # ── Alert banners ──
    if r["id"] in at_risk_ids:
        st.warning("⚠️ **Engagement Alert** — This resident has not engaged with an activity in 14+ days.")
    if r["id"] in declining_ids:
        st.warning("📉 **Declining Mood** — Mood scores have been trending downward recently.")

    st.divider()

    # ── Header ──
    h1, h2 = st.columns([3, 1])
    with h1:
        st.subheader(r["name"])
        room_age = f"Room {r.get('room', '—')}  ·  Age {r.get('age', '—')}"
        if r.get("birthday"):
            room_age += f"  ·  🎂 {r['birthday']}"
        st.caption(room_age)
    with h2:
        st.metric(label="Mobility", value=mob_icon, delta=mob_label, delta_color="off")

    st.divider()

    # ── Main layout ──
    left, right = st.columns([3, 2])

    with left:
        # Care Profile
        with st.container(border=True):
            st.markdown("**Care Profile**")

            st.caption("Conditions & Disabilities")
            if disabilities:
                st.write("  ·  ".join(disabilities))
            else:
                st.caption("_None recorded_")

            st.caption("Cognitive Status")
            st.write(f"{cog_icon}  {cog_level.title()}")

            st.caption("Dietary Requirements")
            dietary_val = (r.get("dietary") or "").strip()
            st.write(dietary_val if dietary_val else "_None recorded_")

        # Personal
        with st.container(border=True):
            st.markdown("**Personal**")

            st.caption("Interests & Hobbies")
            if interests:
                st.write("  ·  ".join(interests))
            else:
                st.caption("_None recorded_")

            st.caption("Staff Notes")
            notes_val = (r.get("notes") or "").strip()
            st.write(notes_val if notes_val else "_No notes recorded_")

            fn = (r.get("family_name") or "").strip()
            fe = (r.get("family_email") or "").strip()
            if fn or fe:
                st.caption("Family Contact")
                st.write(f"{fn}  ·  {fe}" if fn and fe else fn or fe)

        # Quick actions
        st.markdown("**Quick Actions**")
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button("📋 Pre-Brief", key="rc_prebrief",
                         use_container_width=True, type="primary"):
                st.session_state.page = "Pre-Brief"
                st.rerun()
        with qa2:
            if st.button("📅 Calendar", key="rc_cal", use_container_width=True):
                st.session_state.page = "Calendar"
                st.rerun()
        with qa3:
            if st.button("👨‍👩‍👧 Family", key="rc_family", use_container_width=True):
                st.session_state.page = "Family Updates"
                st.rerun()

    with right:
        # Engagement
        with st.container(border=True):
            st.caption("ENGAGEMENT")
            if eng_rate is not None:
                st.progress(eng_rate / 100, text=f"{eng_rate}% engagement rate")
            else:
                st.caption("No engagement data yet")
            st.caption(f"{total_sessions} sessions total  ·  {engaged_count} engaged")

        # Mood trend
        with st.container(border=True):
            st.caption("MOOD TREND — LAST 8 SESSIONS")
            if trend:
                emojis = " ".join(
                    MOOD_EMOJI.get(e.get("mood_after") or 3, "😐") for e in trend
                )
                st.write(emojis)
                st.caption("😔 Very Low  →  😊 Great  (oldest to newest)")
            else:
                st.caption("No mood data yet")

        # Last activity
        with st.container(border=True):
            st.caption("LAST ACTIVITY")
            st.write(last_str)

        # AI Profile Assistant
        with st.container(border=True):
            st.caption("PROFILE ASSISTANT")
            st.write(
                "Profile fields empty or incomplete? Generate a realistic "
                "sample profile with AI to use as a starting point."
            )

        gen_key = f"ai_profile_{r['id']}"
        if st.button("✨ Generate Sample Profile", key=f"gen_btn_{r['id']}",
                     use_container_width=True):
            with st.spinner("Generating profile..."):
                result = _generate_ai_profile(r)
            if result:
                st.session_state[gen_key] = result

        if st.session_state.get(gen_key):
            p = st.session_state[gen_key]
            cog_ai = (p.get("cognitive") or "intact").lower()
            with st.container(border=True):
                st.caption("✨ AI-SUGGESTED PROFILE")

                st.caption("CONDITIONS")
                st.write(p.get("disabilities") or "—")

                st.caption("COGNITIVE")
                st.write(f"{COGNITIVE_COLOR.get(cog_ai, '⚪')}  {cog_ai.title()}")

                st.caption("DIETARY")
                st.write(p.get("dietary") or "None")

                st.caption("INTERESTS")
                st.write(p.get("special_needs") or "—")

                st.caption("STAFF NOTES")
                notes_ai = (p.get("notes") or "").strip()
                st.write(notes_ai if notes_ai else "—")

            save_col, discard_col = st.columns(2)
            with save_col:
                if st.button("💾 Save to Profile", key=f"save_prof_{r['id']}",
                             type="primary", use_container_width=True):
                    merged = {
                        "name":         r.get("name", ""),
                        "age":          r.get("age", ""),
                        "room":         r.get("room", ""),
                        "birthday":     r.get("birthday", ""),
                        "mobility":     r.get("mobility", "independent"),
                        "cognitive":    p.get("cognitive", r.get("cognitive", "intact")),
                        "dietary":      p.get("dietary", r.get("dietary", "")),
                        "disabilities": p.get("disabilities", r.get("disabilities", "")),
                        "special_needs": p.get("special_needs", r.get("special_needs", "")),
                        "notes":        p.get("notes", r.get("notes", "")),
                    }
                    save_resident(merged, resident_id=r["id"])
                    st.session_state.pop(gen_key, None)
                    st.success("Profile saved!")
                    st.rerun()
            with discard_col:
                if st.button("✕ Discard", key=f"disc_prof_{r['id']}",
                             use_container_width=True):
                    st.session_state.pop(gen_key, None)
                    st.rerun()

        # Recent sessions
        with st.container(border=True):
            st.caption("RECENT SESSIONS")
            recent = engs[:8]
            if not recent:
                st.caption("No sessions recorded yet.")
            else:
                for e in recent:
                    icon   = "✅" if e["engaged"] else "❌"
                    mood_a = MOOD_EMOJI.get(e.get("mood_after"), "")
                    rating = "⭐" * (e.get("rating") or 0) if e.get("rating") else ""
                    note   = (e.get("staff_note") or "").strip()
                    col_main, col_right = st.columns([4, 1])
                    with col_main:
                        st.markdown(f"{icon} **{e['event_date']}** — {e['event_title']}")
                        if note:
                            st.caption(note)
                    with col_right:
                        suffix = f"{mood_a} {rating}".strip()
                        if suffix:
                            st.write(suffix)
                    st.divider()
