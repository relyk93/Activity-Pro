import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

def get_smtp_config():
    """Get SMTP config from Streamlit secrets or environment."""
    try:
        return {
            "host": st.secrets.get("SMTP_HOST", "smtp.gmail.com"),
            "port": int(st.secrets.get("SMTP_PORT", 587)),
            "user": st.secrets.get("SMTP_USER", ""),
            "password": st.secrets.get("SMTP_PASSWORD", ""),
            "from_email": st.secrets.get("FROM_EMAIL", ""),
        }
    except Exception:
        return {"host": "", "port": 587, "user": "", "password": "", "from_email": ""}

def send_email(to_email, subject, html_body, plain_body=""):
    """Send an HTML email. Returns (success: bool, message: str)."""
    config = get_smtp_config()
    if not config["user"] or not config["password"]:
        return False, "Email not configured. Add SMTP settings to .streamlit/secrets.toml"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["from_email"] or config["user"]
        msg["To"] = to_email

        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(config["user"], config["password"])
            server.sendmail(config["from_email"] or config["user"], to_email, msg.as_string())

        return True, f"Email sent to {to_email}"
    except Exception as e:
        return False, f"Email failed: {str(e)}"

def build_family_update_html(resident, engagements, facility_name="ActivityPro Facility"):
    """Build a beautiful HTML family update email."""
    total = len(engagements)
    engaged = sum(1 for e in engagements if e['engaged'])
    rate = int(engaged / total * 100) if total else 0
    avg_mood_before = sum(e.get('mood_before') or 3 for e in engagements) / total if total else 3
    avg_mood_after = sum(e.get('mood_after') or 3 for e in engagements) / total if total else 3
    mood_delta = round(avg_mood_after - avg_mood_before, 1)
    mood_phrase = "improving" if mood_delta > 0 else "stable" if mood_delta == 0 else "needs attention"

    recent = engagements[:5]
    activity_rows = ""
    for eng in recent:
        icon = "✅" if eng['engaged'] else "❌"
        stars = "⭐" * (eng.get('rating') or 0) or "—"
        note = f"<br><em style='color:#718096; font-size:13px;'>{eng['staff_note']}</em>" if eng.get('staff_note') else ""
        activity_rows += f"""
        <tr>
            <td style='padding:10px; border-bottom:1px solid #F0EDE8;'>{eng['event_date']}</td>
            <td style='padding:10px; border-bottom:1px solid #F0EDE8;'>{eng['event_title']}{note}</td>
            <td style='padding:10px; border-bottom:1px solid #F0EDE8; text-align:center;'>{icon}</td>
            <td style='padding:10px; border-bottom:1px solid #F0EDE8; text-align:center;'>{stars}</td>
        </tr>"""

    bar_color = "#7C9A7E" if rate >= 70 else "#D4A843" if rate >= 40 else "#C47B5A"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style='margin:0; padding:0; background:#FAF7F2; font-family: Georgia, serif;'>
  <div style='max-width:600px; margin:0 auto; background:#FFFDF9; border-radius:16px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,0.08);'>

    <!-- Header -->
    <div style='background:linear-gradient(135deg, #4A6B4C, #7C9A7E); padding:40px 32px; text-align:center;'>
      <div style='font-size:32px; margin-bottom:8px;'>🌸</div>
      <h1 style='margin:0; color:white; font-size:24px; font-weight:400; letter-spacing:1px;'>Activity Update</h1>
      <p style='margin:8px 0 0; color:#D4F5D4; font-size:14px;'>{facility_name} · {date.today().strftime("%B %Y")}</p>
    </div>

    <!-- Greeting -->
    <div style='padding:32px 32px 0;'>
      <p style='font-size:18px; color:#1A2332; margin:0 0 8px;'>Dear Family of <strong>{resident['name']}</strong>,</p>
      <p style='color:#4A5568; line-height:1.7; margin:0;'>
        We're delighted to share this month's activity update for {resident['name'].split()[0]}.
        Our team works hard to ensure every resident feels engaged, joyful, and cared for each day.
      </p>
    </div>

    <!-- Stats -->
    <div style='padding:24px 32px;'>
      <table style='width:100%; border-collapse:collapse;'>
        <tr>
          <td style='width:33%; text-align:center; padding:16px; background:#F5F9F5; border-radius:12px; margin:4px;'>
            <div style='font-size:28px; font-weight:700; color:{bar_color};'>{rate}%</div>
            <div style='font-size:12px; color:#718096; text-transform:uppercase; letter-spacing:1px; margin-top:4px;'>Engagement Rate</div>
          </td>
          <td style='width:4px;'></td>
          <td style='width:33%; text-align:center; padding:16px; background:#F5F9F5; border-radius:12px;'>
            <div style='font-size:28px; font-weight:700; color:#4A6B4C;'>{total}</div>
            <div style='font-size:12px; color:#718096; text-transform:uppercase; letter-spacing:1px; margin-top:4px;'>Activities Attended</div>
          </td>
          <td style='width:4px;'></td>
          <td style='width:33%; text-align:center; padding:16px; background:#F5F9F5; border-radius:12px;'>
            <div style='font-size:28px; font-weight:700; color:#9B8EC4;'>{"📈" if mood_delta > 0 else "➡️"}</div>
            <div style='font-size:12px; color:#718096; text-transform:uppercase; letter-spacing:1px; margin-top:4px;'>Mood {mood_phrase.title()}</div>
          </td>
        </tr>
      </table>
    </div>

    <!-- Activity Log -->
    <div style='padding:0 32px 24px;'>
      <h3 style='color:#1A2332; font-size:16px; margin:0 0 16px; font-weight:600;'>Recent Activity Log</h3>
      <table style='width:100%; border-collapse:collapse; font-size:14px; color:#4A5568;'>
        <thead>
          <tr style='background:#F5F9F5;'>
            <th style='padding:10px; text-align:left; font-weight:600; color:#1A2332;'>Date</th>
            <th style='padding:10px; text-align:left; font-weight:600; color:#1A2332;'>Activity</th>
            <th style='padding:10px; text-align:center; font-weight:600; color:#1A2332;'>Engaged</th>
            <th style='padding:10px; text-align:center; font-weight:600; color:#1A2332;'>Rating</th>
          </tr>
        </thead>
        <tbody>{activity_rows}</tbody>
      </table>
    </div>

    <!-- Footer -->
    <div style='background:#F5F9F5; padding:24px 32px; text-align:center; border-top:1px solid #E2DDD6;'>
      <p style='color:#718096; font-size:13px; margin:0 0 8px;'>Questions about {resident['name'].split()[0]}'s care? We'd love to hear from you.</p>
      <p style='color:#4A6B4C; font-size:13px; margin:0;'>💚 Sent with care by <strong>{facility_name}</strong> Activity Team · Powered by ActivityPro</p>
    </div>
  </div>
</body>
</html>"""

def build_staff_reminder_html(events, facility_name="ActivityPro Facility"):
    """Build daily staff reminder email."""
    event_rows = ""
    for ev in events:
        cat = ev.get('category', 'social')
        is_special = ev.get('group_type') == 'special_needs'
        group_label = "🟣 Special Needs" if is_special else "👥 All Residents"
        event_rows += f"""
        <tr>
          <td style='padding:12px; border-bottom:1px solid #F0EDE8; font-weight:600; color:#1A2332;'>{ev.get('time','TBD')}</td>
          <td style='padding:12px; border-bottom:1px solid #F0EDE8;'>{ev['title']}</td>
          <td style='padding:12px; border-bottom:1px solid #F0EDE8; color:#718096;'>{ev.get('location','Activity Room')}</td>
          <td style='padding:12px; border-bottom:1px solid #F0EDE8;'>{group_label}</td>
          <td style='padding:12px; border-bottom:1px solid #F0EDE8; color:#7C9A7E;'>💰 {ev.get('cost_estimate','Free')}</td>
        </tr>"""

    return f"""
<!DOCTYPE html>
<html>
<body style='margin:0; padding:0; background:#FAF7F2; font-family:sans-serif;'>
  <div style='max-width:600px; margin:0 auto; background:#FFFDF9; border-radius:16px; overflow:hidden;'>
    <div style='background:linear-gradient(135deg, #2C3E50, #4A6B4C); padding:32px; text-align:center;'>
      <div style='font-size:28px;'>☀️</div>
      <h1 style='margin:8px 0 0; color:white; font-size:20px; font-weight:400;'>Today's Activity Schedule</h1>
      <p style='margin:6px 0 0; color:#A0C4B0; font-size:14px;'>{date.today().strftime("%A, %B %d, %Y")} · {facility_name}</p>
    </div>
    <div style='padding:24px 32px;'>
      <p style='color:#4A5568;'>Good morning! Here are today's planned activities. Have a wonderful day with your residents. 🌸</p>
      <table style='width:100%; border-collapse:collapse; font-size:14px;'>
        <thead>
          <tr style='background:#F5F9F5;'>
            <th style='padding:10px; text-align:left; color:#1A2332;'>Time</th>
            <th style='padding:10px; text-align:left; color:#1A2332;'>Activity</th>
            <th style='padding:10px; text-align:left; color:#1A2332;'>Location</th>
            <th style='padding:10px; text-align:left; color:#1A2332;'>Group</th>
            <th style='padding:10px; text-align:left; color:#1A2332;'>Cost</th>
          </tr>
        </thead>
        <tbody>{event_rows}</tbody>
      </table>
    </div>
    <div style='background:#F5F9F5; padding:20px 32px; text-align:center; border-top:1px solid #E2DDD6;'>
      <p style='color:#718096; font-size:13px; margin:0;'>💚 ActivityPro · {facility_name}</p>
    </div>
  </div>
</body>
</html>"""
