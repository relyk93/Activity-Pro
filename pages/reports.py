import streamlit as st
from utils.auth import require_pro
from utils.database import get_residents, get_engagements, get_events
from datetime import date, timedelta
import plotly.graph_objects as go
import plotly.express as px

def show():
    st.markdown("# 📊 Reports & Analytics")

    if not require_pro():
        return

    st.markdown("<div style='color:#718096; margin-bottom:20px;'>Generate participation reports for care planning, family updates, and administration.</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Resident Report", "📅 Monthly Summary", "🏆 Activity Effectiveness", "📈 Trend Charts"])

    # ─── Tab 1: Resident Report ───
    with tab1:
        residents = get_residents()
        resident_map = {r['name']: r for r in residents}
        selected = st.selectbox("Select Resident", list(resident_map.keys()))
        r = resident_map[selected]

        engs = get_engagements(resident_id=r['id'])

        if not engs:
            st.info(f"No engagement data recorded for {r['name']} yet.")
        else:
            total = len(engs)
            engaged = sum(1 for e in engs if e['engaged'])
            avg_rating = sum(e.get('rating') or 0 for e in engs) / total if total else 0
            avg_mood_before = sum(e.get('mood_before') or 3 for e in engs) / total if total else 3
            avg_mood_after = sum(e.get('mood_after') or 3 for e in engs) / total if total else 3

            st.markdown(f"### 📋 Participation Report: {r['name']}")
            st.markdown(f"*Generated {date.today().strftime('%B %d, %Y')}*")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""<div class='metric-box'><div class='metric-number'>{total}</div><div class='metric-label'>Total Sessions</div></div>""", unsafe_allow_html=True)
            with col2:
                rate = int(engaged/total*100) if total else 0
                st.markdown(f"""<div class='metric-box'><div class='metric-number'>{rate}%</div><div class='metric-label'>Engagement Rate</div></div>""", unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class='metric-box'><div class='metric-number'>{round(avg_rating,1)}⭐</div><div class='metric-label'>Avg Rating</div></div>""", unsafe_allow_html=True)
            with col4:
                mood_delta = round(avg_mood_after - avg_mood_before, 1)
                delta_icon = "📈" if mood_delta > 0 else "📉" if mood_delta < 0 else "➡️"
                st.markdown(f"""<div class='metric-box'><div class='metric-number'>{delta_icon} {'+' if mood_delta > 0 else ''}{mood_delta}</div><div class='metric-label'>Avg Mood Change</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Resident Profile")
            disabilities = r.get('disabilities','') or 'None'
            st.markdown(f"""
            <div class='ap-card'>
                <div style='display:grid; grid-template-columns:1fr 1fr; gap:12px;'>
                    <div><strong>Mobility:</strong> {r.get('mobility','?').title()}</div>
                    <div><strong>Cognitive:</strong> {r.get('cognitive','?').replace('_',' ').title()}</div>
                    <div><strong>Dietary:</strong> {r.get('dietary','None') or 'None'}</div>
                    <div><strong>Room:</strong> {r.get('room','?')}</div>
                    <div style='grid-column:1/-1;'><strong>Disabilities:</strong> {disabilities}</div>
                    <div style='grid-column:1/-1;'><strong>Interests:</strong> {r.get('special_needs','') or '—'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Activity Log")
            for eng in engs:
                engaged_icon = "✅" if eng['engaged'] else "❌"
                stars = "⭐" * (eng.get('rating') or 0) or "—"
                mood_b = eng.get('mood_before') or '?'
                mood_a = eng.get('mood_after') or '?'
                note = eng.get('staff_note','') or ''
                st.markdown(f"""
                <div style='padding:10px 16px; background:#FFFDF9; border-radius:10px; border:1px solid #E2DDD6; margin-bottom:8px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <strong>{eng['event_title']}</strong>
                        <span style='color:#718096; font-size:0.85rem;'>{eng['event_date']}</span>
                    </div>
                    <div style='font-size:0.85rem; color:#4A5568; margin-top:4px;'>
                        {engaged_icon} &nbsp;|&nbsp; {stars} &nbsp;|&nbsp; Mood: {mood_b} → {mood_a}
                        {f"<br><em style='color:#718096;'>{note}</em>" if note else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Care plan summary
            st.markdown("#### Care Plan Summary")
            top_activities = [e['event_title'] for e in engs if e['engaged']][:3]
            st.markdown(f"""
            <div class='ap-card ap-card-sage'>
                <strong>For Care Plan Documentation:</strong><br><br>
                {r['name']} has participated in {total} structured activity sessions with a {rate}% engagement rate.
                {'Activities appear to have a positive mood impact (avg +' + str(mood_delta) + ').' if mood_delta > 0 else 'Mood impact is neutral to slightly negative — consider adjusting activity types.'}
                {'Top engaging activities include: ' + ', '.join(top_activities) + '.' if top_activities else ''}
                Disabilities/needs on record: {disabilities}.
                {'Recommend continued participation with adaptations for ' + disabilities + '.' if disabilities and disabilities != 'None' else 'No special adaptations currently required.'}
            </div>
            """, unsafe_allow_html=True)

    # ─── Tab 2: Monthly Summary ───
    with tab2:
        st.markdown("### 📅 Monthly Facility Report")

        month_start = date.today().replace(day=1)
        month_end = date.today()
        events = get_events(date_from=str(month_start), date_to=str(month_end))
        all_engs = get_engagements()

        month_engs = [e for e in all_engs if e['event_date'] >= str(month_start)]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class='metric-box'><div class='metric-number'>{len(events)}</div><div class='metric-label'>Activities This Month</div></div>""", unsafe_allow_html=True)
        with col2:
            eng_count = sum(1 for e in month_engs if e['engaged'])
            total_count = len(month_engs)
            rate = int(eng_count/total_count*100) if total_count else 0
            st.markdown(f"""<div class='metric-box'><div class='metric-number'>{rate}%</div><div class='metric-label'>Monthly Engagement</div></div>""", unsafe_allow_html=True)
        with col3:
            residents = get_residents()
            st.markdown(f"""<div class='metric-box'><div class='metric-number'>{len(residents)}</div><div class='metric-label'>Active Residents</div></div>""", unsafe_allow_html=True)

        st.markdown("#### Activities by Category")
        cat_counts = {}
        for ev in events:
            cat = ev.get('category','social')
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        if cat_counts:
            for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
                pct = int(count / len(events) * 100)
                st.markdown(f"""
                <div style='margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between; font-size:0.85rem; color:#4A5568;'>
                        <span class='tag tag-{cat}'>{cat.title()}</span><span>{count} sessions ({pct}%)</span>
                    </div>
                    <div style='background:#E2DDD6; border-radius:6px; height:8px; margin-top:4px;'>
                        <div style='background:#7C9A7E; width:{pct}%; border-radius:6px; height:8px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ─── Tab 3: Activity Effectiveness ───
    with tab3:
        st.markdown("### 🏆 Most Effective Activities")
        st.markdown("<div style='color:#718096; margin-bottom:16px;'>Ranked by resident engagement and mood improvement</div>", unsafe_allow_html=True)

        all_engs = get_engagements()

        activity_stats = {}
        for eng in all_engs:
            title = eng['event_title']
            if title not in activity_stats:
                activity_stats[title] = {"total": 0, "engaged": 0, "ratings": [], "mood_deltas": []}
            activity_stats[title]["total"] += 1
            if eng['engaged']:
                activity_stats[title]["engaged"] += 1
            if eng.get('rating'):
                activity_stats[title]["ratings"].append(eng['rating'])
            if eng.get('mood_before') and eng.get('mood_after'):
                activity_stats[title]["mood_deltas"].append(eng['mood_after'] - eng['mood_before'])

        ranked = []
        for title, stats in activity_stats.items():
            if stats['total'] > 0:
                rate = int(stats['engaged'] / stats['total'] * 100)
                avg_rating = sum(stats['ratings']) / len(stats['ratings']) if stats['ratings'] else 0
                avg_mood = sum(stats['mood_deltas']) / len(stats['mood_deltas']) if stats['mood_deltas'] else 0
                score = rate * 0.5 + avg_rating * 10 * 0.3 + (avg_mood * 10 + 50) * 0.2
                ranked.append({"title": title, "rate": rate, "avg_rating": round(avg_rating,1),
                               "avg_mood": round(avg_mood,1), "total": stats['total'], "score": round(score,1)})

        ranked.sort(key=lambda x: -x['score'])

        if ranked:
            for i, act in enumerate(ranked):
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
                mood_icon = "📈" if act['avg_mood'] > 0 else "📉" if act['avg_mood'] < 0 else "➡️"
                st.markdown(f"""
                <div class='ap-card' style='margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:1.3rem;'>{medal}</span>
                            <strong style='font-size:1rem; margin-left:8px;'>{act['title']}</strong>
                        </div>
                        <div style='text-align:right;'>
                            <strong style='color:#7C9A7E; font-size:1.1rem;'>{act['rate']}%</strong>
                            <span style='color:#A0AEC0; font-size:0.8rem;'> engaged</span>
                        </div>
                    </div>
                    <div style='font-size:0.82rem; color:#4A5568; margin-top:6px; display:flex; gap:16px;'>
                        <span>📊 {act['total']} sessions</span>
                        <span>⭐ {act['avg_rating']}/5</span>
                        <span>{mood_icon} Mood: {'+' if act['avg_mood'] > 0 else ''}{act['avg_mood']}</span>
                        <span>📈 Score: {act['score']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Rate some activities to see effectiveness rankings here!")

    # ─── Tab 4: Trend Charts ───
    with tab4:
        st.markdown("### 📈 Mood & Engagement Trends")

        all_engs = get_engagements()
        residents = get_residents()
        resident_map = {r['id']: r['name'] for r in residents}

        if not all_engs:
            st.info("No engagement data yet. Start rating activities to see trends here.")
        else:
            # ── Mood over time per resident ──
            st.markdown("#### Mood Over Time")
            selected_resident = st.selectbox(
                "Select resident for mood trend",
                options=[r['id'] for r in residents],
                format_func=lambda rid: resident_map[rid],
                key="trend_resident"
            )
            resident_engs = [e for e in all_engs if e['resident_id'] == selected_resident
                             and e.get('mood_before') and e.get('mood_after')]

            if resident_engs:
                dates = [e['event_date'] for e in resident_engs]
                mood_before = [e['mood_before'] for e in resident_engs]
                mood_after  = [e['mood_after']  for e in resident_engs]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates, y=mood_before, mode='lines+markers',
                    name='Mood Before', line=dict(color='#9B8EC4', width=2),
                    marker=dict(size=8)
                ))
                fig.add_trace(go.Scatter(
                    x=dates, y=mood_after, mode='lines+markers',
                    name='Mood After', line=dict(color='#7C9A7E', width=2),
                    marker=dict(size=8)
                ))
                fig.update_layout(
                    yaxis=dict(tickvals=[1,2,3,4,5],
                               ticktext=["😔 Very Low","😕 Low","😐 Neutral","🙂 Good","😊 Great"],
                               range=[0.5, 5.5]),
                    xaxis_title="Session Date",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=320
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No mood data for {resident_map[selected_resident]} yet.")

            st.markdown("---")

            # ── Engagement rate by day of week ──
            st.markdown("#### Engagement by Day of Week")
            from datetime import datetime as dt
            day_stats = {d: {"total": 0, "engaged": 0} for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]}
            day_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            for e in all_engs:
                try:
                    dow = dt.strptime(e['event_date'], "%Y-%m-%d").strftime("%a")
                    day_stats[dow]["total"] += 1
                    if e['engaged']:
                        day_stats[dow]["engaged"] += 1
                except Exception:
                    pass

            days = [d for d in day_order if day_stats[d]["total"] > 0]
            rates = [int(day_stats[d]["engaged"] / day_stats[d]["total"] * 100) if day_stats[d]["total"] else 0 for d in days]

            if days:
                fig2 = go.Figure(go.Bar(
                    x=days, y=rates,
                    marker_color=['#7C9A7E' if r >= 70 else '#D4A843' if r >= 40 else '#C47B5A' for r in rates],
                    text=[f"{r}%" for r in rates],
                    textposition='outside'
                ))
                fig2.update_layout(
                    yaxis=dict(title="Engagement Rate (%)", range=[0, 110]),
                    xaxis_title="Day of Week",
                    margin=dict(l=20, r=20, t=20, b=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=280
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")

            # ── Activity category breakdown (pie) ──
            st.markdown("#### Sessions by Category")
            events = get_events()
            cat_counts = {}
            for ev in events:
                cat = ev.get('category', 'social') or 'social'
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            if cat_counts:
                colors = {'physical':'#DEF0DE','cognitive':'#DDE8F5','social':'#F5DDDE',
                          'creative':'#F5EDDD','mindful':'#EBE4F5'}
                fig3 = px.pie(
                    names=list(cat_counts.keys()),
                    values=list(cat_counts.values()),
                    color=list(cat_counts.keys()),
                    color_discrete_map=colors
                )
                fig3.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=300
                )
                st.plotly_chart(fig3, use_container_width=True)
