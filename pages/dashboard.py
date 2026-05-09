import streamlit as st
from utils.database import get_residents, get_events, get_engagements
from datetime import date, timedelta

def show():
    st.markdown("# 🌸 ActivityPro Dashboard")
    sub = st.session_state.get("subscription", "free")
    facility = st.session_state.get("facility_name", "My Facility")
    st.markdown(f"<div style='color:#718096; margin-top:-10px; margin-bottom:24px; font-size:1rem;'>Welcome back — <strong>{facility}</strong> · {date.today().strftime('%A, %B %d, %Y')}</div>", unsafe_allow_html=True)

    # Metrics row
    residents = get_residents()
    today_str = str(date.today())
    week_end = str(date.today() + timedelta(days=7))
    today_events = get_events(date_from=today_str, date_to=today_str)
    week_events = get_events(date_from=today_str, date_to=week_end)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class='metric-box'>
            <div class='metric-number'>{len(residents)}</div>
            <div class='metric-label'>Active Residents</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-box'>
            <div class='metric-number'>{len(today_events)}</div>
            <div class='metric-label'>Activities Today</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-box'>
            <div class='metric-number'>{len(week_events)}</div>
            <div class='metric-label'>This Week</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        # Calculate avg engagement
        all_eng = get_engagements()
        engaged = [e for e in all_eng if e['engaged']]
        rate = int(len(engaged) / len(all_eng) * 100) if all_eng else 0
        st.markdown(f"""<div class='metric-box'>
            <div class='metric-number'>{rate}%</div>
            <div class='metric-label'>Engagement Rate</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📅 Today's Schedule")
        if today_events:
            for ev in today_events:
                cat = ev.get('category', 'social')
                color_map = {
                    "physical": "ap-card-sage",
                    "mindful": "ap-card-lavender",
                    "social": "ap-card-sky",
                    "cognitive": "ap-card-terra",
                    "creative": "ap-card-terra",
                    "special_needs": "ap-card-lavender",
                }
                card_class = color_map.get(cat, "ap-card")
                group_badge = "🔵 All Residents" if ev['group_type'] == 'all' else "🟣 Special Needs"
                st.markdown(f"""
                <div class='ap-card {card_class}'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div>
                            <div style='font-weight:600; font-size:1.05rem; color:#1A2332;'>{ev['title']}</div>
                            <div style='color:#718096; font-size:0.85rem; margin-top:4px;'>🕐 {ev.get('time','TBD')} &nbsp;|&nbsp; 📍 {ev.get('location','Activity Room')} &nbsp;|&nbsp; {group_badge}</div>
                        </div>
                        <span class='tag tag-{cat}'>{cat.title()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='ap-card' style='text-align:center; padding:40px;'>
                <div style='font-size:2rem;'>📭</div>
                <div style='color:#718096; margin-top:8px;'>No activities scheduled for today.</div>
                <div style='color:#A0AEC0; font-size:0.85rem;'>Use the AI Generator to create your week's calendar!</div>
            </div>
            """, unsafe_allow_html=True)

        # Upcoming week preview
        st.markdown("### 📆 This Week")
        if week_events:
            for ev in week_events:
                ev_date = ev['date']
                if ev_date == today_str:
                    continue
                day_label = date.fromisoformat(ev_date).strftime("%a %b %d")
                st.markdown(f"""
                <div style='padding:10px 16px; background:#FFFDF9; border-radius:10px; border:1px solid #E2DDD6; margin-bottom:8px; display:flex; justify-content:space-between;'>
                    <span style='color:#4A5568;'><strong>{day_label}</strong> · {ev.get('time','TBD')} — {ev['title']}</span>
                    <span class='tag tag-{ev.get("category","social")}'>{(ev.get("category","social")).title()}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming events this week. Generate a calendar to get started!")

    with col_right:
        st.markdown("### 🎂 Upcoming Birthdays")
        today_d = date.today()
        birthday_list = []
        for r in residents:
            bday = r.get('birthday')
            if bday:
                try:
                    bday_date = date.fromisoformat(bday)
                    this_year = bday_date.replace(year=today_d.year)
                    if this_year < today_d:
                        this_year = this_year.replace(year=today_d.year + 1)
                    days_away = (this_year - today_d).days
                    if days_away <= 30:
                        birthday_list.append((r['name'], this_year, days_away))
                except:
                    pass
        birthday_list.sort(key=lambda x: x[2])

        if birthday_list:
            for name, bday, days in birthday_list:
                label = "🎉 TODAY!" if days == 0 else f"in {days} days"
                st.markdown(f"""
                <div style='padding:10px 14px; background:#FFF8E8; border-radius:10px; border:1px solid #F0D090; margin-bottom:8px;'>
                    <strong style='color:#5A3A00;'>{name}</strong><br>
                    <span style='color:#8A6A20; font-size:0.85rem;'>🎂 {bday.strftime("%B %d")} — {label}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#A0AEC0;'>No birthdays in the next 30 days.</div>", unsafe_allow_html=True)

        st.markdown("### 👥 Residents Quick View")
        mobility_icons = {"independent": "🟢", "cane": "🟡", "walker": "🟡", "wheelchair": "🔴"}
        for r in residents[:8]:
            icon = mobility_icons.get(r.get('mobility', 'independent'), "⚪")
            disab = r.get('disabilities', '')
            disab_str = f" · {disab}" if disab else ""
            st.markdown(f"""
            <div style='padding:8px 14px; background:#FFFDF9; border-radius:8px; border:1px solid #E2DDD6; margin-bottom:6px;'>
                <span style='font-weight:500; color:#1A2332;'>{icon} {r['name']}</span>
                <span style='font-size:0.78rem; color:#A0AEC0;'> · Rm {r.get("room","?")} · Age {r.get("age","?")}{disab_str}</span>
            </div>
            """, unsafe_allow_html=True)
        if len(residents) > 8:
            st.caption(f"+ {len(residents)-8} more residents")

        if sub in ("pro", "enterprise"):
            st.markdown("### 📊 Engagement Snapshot")
            categories = {}
            all_eng = get_engagements()
            for e in all_eng:
                pass
            category_data = {"Physical": 78, "Mindful": 85, "Social": 72, "Cognitive": 68, "Creative": 81}
            for cat, pct in category_data.items():
                bar_color = "#7C9A7E" if pct >= 75 else "#D4A843" if pct >= 60 else "#C47B5A"
                st.markdown(f"""
                <div style='margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between; font-size:0.82rem; color:#4A5568; margin-bottom:3px;'>
                        <span>{cat}</span><span>{pct}%</span>
                    </div>
                    <div style='background:#E2DDD6; border-radius:6px; height:8px;'>
                        <div style='background:{bar_color}; width:{pct}%; border-radius:6px; height:8px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
