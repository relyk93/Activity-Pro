import streamlit as st
from utils.database import get_events, get_residents, save_engagement, get_engagements, save_photo, get_photos, delete_photo, PHOTOS_DIR
from utils.auth import get_current_staff
from datetime import date, timedelta
import os
import uuid

MOOD_LABELS = {1: "😔 Very Low", 2: "😕 Low", 3: "😐 Neutral", 4: "🙂 Good", 5: "😊 Great"}

def show():
    st.markdown("# ⭐ Rate Activities")
    st.markdown("<div style='color:#718096; margin-bottom:20px;'>Record resident participation and engagement for each activity session.</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 Record Engagement", "📊 Engagement Summary"])

    with tab1:
        # Select event
        past_week = str(date.today() - timedelta(days=14))
        today_str = str(date.today())
        events = get_events(date_from=past_week, date_to=today_str)

        if not events:
            st.info("No recent events found. Add activities to the calendar first.")
            return

        # Pre-select if coming from calendar
        pre_selected_id = st.session_state.get("rate_event_id")
        event_options = {f"{ev['date']} — {ev['title']}": ev for ev in events}
        default_idx = 0
        if pre_selected_id:
            for i, ev in enumerate(events):
                if ev['id'] == pre_selected_id:
                    default_idx = i
                    break

        selected_event_label = st.selectbox("Select Activity Session", list(event_options.keys()), index=default_idx)
        selected_event = event_options[selected_event_label]
        st.session_state.rate_event_id = None  # Clear

        ev = selected_event
        cat = ev.get('category', 'social')
        is_special = ev.get('group_type') == 'special_needs'

        st.markdown(f"""
        <div class='ap-card {"ap-card-lavender" if is_special else "ap-card-sage"}'>
            <strong style='font-size:1.1rem;'>{'🟣 ' if is_special else ''}{ev['title']}</strong><br>
            <span style='color:#718096; font-size:0.85rem;'>📅 {ev['date']} · 🕐 {ev.get('time','TBD')} · 📍 {ev.get('location','Activity Room')} · <span class='tag tag-{cat}'>{cat.title()}</span></span>
        </div>
        """, unsafe_allow_html=True)

        # Overall session rating
        st.markdown("#### Session Overview")
        col1, col2 = st.columns(2)
        with col1:
            session_rating = st.slider("Overall session quality", 1, 5, 3,
                format="%d ⭐", key=f"session_rating_{ev['id']}")
        with col2:
            session_notes = st.text_area("Session notes (optional)",
                placeholder="e.g. Great energy today, residents really enjoyed the music portion...",
                key=f"session_notes_{ev['id']}")

        st.markdown("---")
        st.markdown("#### 👥 Individual Resident Engagement")

        residents = get_residents()
        if is_special:
            residents = [r for r in residents if r.get('disabilities')]

        existing_engagements = {e['resident_id']: e for e in get_engagements(event_id=ev['id'])}

        if not residents:
            st.info("No residents found.")
            return

        # Batch engagement recording
        engagement_data = {}
        for r in residents:
            existing = existing_engagements.get(r['id'], {})
            with st.expander(f"{'✅' if existing.get('engaged') else '⬜'} **{r['name']}** — Rm {r.get('room','?')} · Age {r.get('age','?')}"):
                disabilities = r.get('disabilities', '') or ''
                if disabilities:
                    disability_tags = " ".join([f"<span class='tag tag-mindful'>{d.strip().title()}</span>"
                                                for d in disabilities.split(',') if d.strip()])
                    st.markdown(disability_tags, unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    engaged = st.radio(
                        "Did they engage?",
                        [True, False],
                        format_func=lambda x: "✅ Engaged" if x else "❌ Did not engage",
                        index=0 if existing.get('engaged', True) else 1,
                        key=f"engaged_{ev['id']}_{r['id']}"
                    )
                with col_b:
                    mood_before = st.select_slider(
                        "Mood BEFORE",
                        options=[1, 2, 3, 4, 5],
                        format_func=lambda x: MOOD_LABELS[x],
                        value=existing.get('mood_before') or 3,
                        key=f"mood_before_{ev['id']}_{r['id']}"
                    )
                with col_c:
                    mood_after = st.select_slider(
                        "Mood AFTER",
                        options=[1, 2, 3, 4, 5],
                        format_func=lambda x: MOOD_LABELS[x],
                        value=existing.get('mood_after') or 3,
                        key=f"mood_after_{ev['id']}_{r['id']}"
                    )

                rating = st.slider(
                    "Activity rating for this resident",
                    0, 5, existing.get('rating') or 0,
                    format="%d ⭐",
                    key=f"rating_{ev['id']}_{r['id']}"
                )

                staff_note = st.text_input(
                    "Staff observation (optional)",
                    value=existing.get('staff_note', '') or '',
                    placeholder="e.g. Margaret smiled throughout, asked to do it again...",
                    key=f"note_{ev['id']}_{r['id']}"
                )

                engagement_data[r['id']] = {
                    "event_id": ev['id'],
                    "resident_id": r['id'],
                    "engaged": engaged,
                    "rating": rating,
                    "mood_before": mood_before,
                    "mood_after": mood_after,
                    "staff_note": staff_note,
                }

        if st.button("💾 Save All Engagement Records", type="primary", use_container_width=True):
            for res_id, eng in engagement_data.items():
                save_engagement(eng)
            st.success(f"✅ Saved engagement records for {len(engagement_data)} residents!")
            st.balloons()

        # ── Photo Documentation ──
        st.markdown("---")
        st.markdown("#### 📸 Session Photos")
        st.markdown("<div style='color:#718096; font-size:0.85rem; margin-bottom:12px;'>Upload photos from this session for documentation and family updates.</div>", unsafe_allow_html=True)

        # Existing photos
        existing_photos = get_photos(event_id=ev['id'])
        if existing_photos:
            photo_cols = st.columns(min(len(existing_photos), 4))
            for i, photo in enumerate(existing_photos):
                photo_path = os.path.join(PHOTOS_DIR, photo['filename'])
                if os.path.exists(photo_path):
                    with photo_cols[i % 4]:
                        st.image(photo_path, use_container_width=True)
                        caption = photo.get('caption') or ''
                        if caption:
                            st.caption(caption)
                        if st.button("🗑️", key=f"del_photo_{photo['id']}", help="Delete photo"):
                            delete_photo(photo['id'])
                            st.rerun()

        # Upload new photos
        staff = get_current_staff()
        uploaded = st.file_uploader(
            "Add photos (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key=f"photo_upload_{ev['id']}"
        )
        if uploaded:
            photo_caption = st.text_input("Caption for all uploaded photos (optional)", key=f"photo_caption_{ev['id']}")
            if st.button("📤 Save Photos", key=f"save_photos_{ev['id']}"):
                for f in uploaded:
                    ext = f.name.rsplit('.', 1)[-1].lower()
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    dest = os.path.join(PHOTOS_DIR, filename)
                    with open(dest, 'wb') as out:
                        out.write(f.read())
                    save_photo(ev['id'], None, filename, photo_caption, staff.get('id'))
                st.success(f"✅ {len(uploaded)} photo(s) saved.")
                st.rerun()

    with tab2:
        st.markdown("### 📊 Engagement Summary by Resident")

        residents = get_residents()
        summary_data = []

        for r in residents:
            engs = get_engagements(resident_id=r['id'])
            if engs:
                total = len(engs)
                engaged = sum(1 for e in engs if e['engaged'])
                avg_rating = sum(e.get('rating') or 0 for e in engs) / total
                avg_mood_delta = sum((e.get('mood_after') or 3) - (e.get('mood_before') or 3) for e in engs) / total
                summary_data.append({
                    "resident": r,
                    "total": total,
                    "engaged": engaged,
                    "rate": int(engaged / total * 100),
                    "avg_rating": round(avg_rating, 1),
                    "mood_delta": round(avg_mood_delta, 1)
                })

        if not summary_data:
            st.info("No engagement data recorded yet. Start rating activities to see summaries here.")
            return

        # Sort by engagement rate
        summary_data.sort(key=lambda x: x['rate'], reverse=True)

        for s in summary_data:
            r = s['resident']
            rate = s['rate']
            bar_color = "#7C9A7E" if rate >= 70 else "#D4A843" if rate >= 40 else "#C47B5A"
            mood_icon = "📈" if s['mood_delta'] > 0 else "📉" if s['mood_delta'] < 0 else "➡️"
            stars = "⭐" * int(round(s['avg_rating']))

            st.markdown(f"""
            <div class='ap-card' style='margin-bottom:10px;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <div>
                        <strong style='font-size:1rem;'>{r['name']}</strong>
                        <span style='color:#A0AEC0; font-size:0.8rem;'> · Room {r.get('room','?')} · Age {r.get('age','?')}</span>
                    </div>
                    <div style='text-align:right;'>
                        <span style='font-weight:700; color:{bar_color}; font-size:1.1rem;'>{rate}%</span>
                        <span style='color:#A0AEC0; font-size:0.8rem;'> engaged</span>
                    </div>
                </div>
                <div style='background:#E2DDD6; border-radius:6px; height:10px; margin-bottom:8px;'>
                    <div style='background:{bar_color}; width:{rate}%; border-radius:6px; height:10px;'></div>
                </div>
                <div style='display:flex; gap:20px; font-size:0.82rem; color:#4A5568;'>
                    <span>📊 {s['engaged']}/{s['total']} sessions</span>
                    <span>⭐ Avg rating: {s['avg_rating']}/5 {stars}</span>
                    <span>{mood_icon} Mood impact: {'+' if s['mood_delta'] > 0 else ''}{s['mood_delta']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
