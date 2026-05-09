# 📖 ActivityPro — User Guide

> A complete walkthrough of every feature in ActivityPro, written for activity directors.

---

## Getting Around

ActivityPro has **10 pages** accessible from the left sidebar:

| Page | What it's for |
|------|--------------|
| 🏠 Dashboard | Daily overview, metrics, birthdays |
| 📅 Calendar | Weekly schedule — click any event for full details |
| 🤖 AI Generator | Let AI create your activity calendar |
| 👥 Residents | Add and manage resident profiles |
| ⭐ Rate Activities | Record engagement after each session |
| 📊 Reports | Analytics and care plan documents |
| 🖨️ Print & Export | Printable wall calendars and resident reports |
| 🔔 Notifications | Family emails and staff reminders |
| ⚙️ Settings | Facility name and preferences |
| 💳 Subscription | Manage your plan |

---

## 🏠 Dashboard

Your command center. Every morning, start here.

**What you'll see:**
- **4 metrics** at the top: Active residents, today's activities, this week's count, engagement rate
- **Today's Schedule** — all activities happening today, color-coded by category
- **This Week** — a preview of upcoming activities
- **Upcoming Birthdays** — residents with birthdays in the next 30 days (great for planning!)
- **Residents Quick View** — mobility status at a glance
- **Engagement Snapshot** — which categories residents enjoy most (Pro)

**Tips:**
- Check birthdays weekly to plan celebrations in advance
- The engagement snapshot tells you what's working — lean into high-scoring categories

---

## 📅 Calendar

Your weekly activity grid.

**Navigating:**
- Use **← Previous Week** and **Next Week →** to move through time
- Today is highlighted in green
- Activities are color-coded by category (see legend at bottom)
- 🟣 Purple border = Special Needs group activity

**Clicking an activity:**
- Shows full details: time, location, cost
- **Step-by-step instructions** — share with any staff member
- **Supplies list** — prep ahead of time
- **Accessibility notes** — which disabilities this activity accommodates
- Buttons to Rate, Edit, or Delete the event

**Adding an activity manually:**
- Click **+ Add** on any day
- Choose from your activity library
- Set time, location, and group type

---

## 🤖 AI Generator (Pro)

The heart of ActivityPro. Uses Claude AI to create expert activities.

### Tab 1: Generate Weekly Calendar

Best used Monday morning to plan the week.

1. Set the **week start date**
2. Choose **activities per day** (3 is a good default)
3. Select **focus areas** (balance Physical + Mindful + Social)
4. Set **budget** (most activities are free or under $5)
5. Add any **special occasions** (birthdays, holidays, themes)
6. Click **Generate Weekly Calendar**

The AI creates a full week with:
- Balanced categories across days
- Morning, midday, and afternoon time slots
- Mix of all-resident and special needs activities
- Specific instructions and supply lists for each

Review the preview, then click **Save Entire Week to Calendar**.

### Tab 2: Generate Single Activity

Need one activity fast? Set the category, group, duration, and budget — get a fully detailed activity in seconds.

### Tab 3: Personalized for Resident

Select any resident — the AI reads their disability profile, mobility level, cognitive status, and interests, then creates activities made specifically for them.

*Example: For Dorothy (dementia, wheelchair, loves 1950s music) — the AI might suggest a seated sock-hop, a music memory circle, or a sensory bean bag toss with oldies playing.*

---

## 👥 Residents

### Adding a Resident

1. Click **Add / Edit Resident** tab
2. Fill in name, age, room number, birthday
3. Select **mobility level** — this affects calendar display icons
4. Select **cognitive status** — the AI uses this for activity difficulty
5. Check all applicable **disabilities** from the 19 options
6. Add **interests and hobbies** — the AI reads this to personalize activities
7. Add **private staff notes** — not shared with families

### The 19 Disability Types

ActivityPro understands and adapts to:
Dementia · Alzheimer's · Wheelchair · Limited Mobility · Arthritis · Hearing Loss · Vision Impairment · Parkinson's · Anxiety · Depression · Diabetes · Heart Condition · Osteoporosis · Stroke History · Autism · Dysphagia · Chronic Pain · Incontinence · Fall Risk

### Viewing Engagement History

Expand any resident's card → click **📊 History** to see every activity they've attended, their engagement, ratings, and staff notes.

---

## ⭐ Rate Activities

Record what happened after each session. This is the most important habit for getting value from ActivityPro.

**Best practice:** Rate activities within 2 hours of the session while details are fresh.

### For each resident:
- **Did they engage?** — Yes (✅) or No (❌)
- **Mood Before** — 1 (Very Low) to 5 (Great)
- **Mood After** — same scale
- **Activity Rating** — how well did this activity work for them?
- **Staff Observation** — free text for care notes

*Example note: "Margaret smiled throughout and asked when we're doing this again. She led the last round."*

These notes appear in family emails and care plan reports automatically.

---

## 📊 Reports

### Resident Report
Select any resident to see:
- Engagement rate, sessions attended, average rating, mood impact
- Full activity log with staff notes
- **Care Plan Summary** paragraph (copy-paste ready for clinical documentation)

### Monthly Summary
Facility-wide view:
- Total activities run this month
- Overall engagement rate
- Category breakdown (how much physical vs. mindful vs. social)

### Activity Effectiveness
Ranked list of all activities by engagement + mood improvement score.
Use this to know which activities to run more often and which to replace.

---

## 🖨️ Print & Export

### Weekly Wall Calendar

1. Select the week
2. Click **Generate Printable Calendar**
3. Download the HTML file
4. Open in any browser → **File → Print** → set to **Landscape**
5. Post on the activity board!

The calendar is professionally designed with color-coded categories and is legible from across a room.

### Resident Report

1. Select a resident
2. Click **Generate Report**
3. Download → Print → use for:
   - Care plan binders
   - Family meetings
   - Physician documentation
   - State survey preparation

---

## 🔔 Notifications & Email

### Family Update Emails

Send monthly engagement updates to families automatically.

Each email includes:
- Engagement rate and sessions attended
- Mood improvement statistics
- Recent activity log with staff notes
- Written in warm, family-friendly language

**Setup required:** Add SMTP settings to `.streamlit/secrets.toml` (see [SETUP.md](SETUP.md)).

### Staff Daily Reminder

Send today's activity schedule to staff email every morning.
Great for shift handoffs and keeping everyone informed.

### Low Engagement Alerts

The system flags any resident below 40% engagement.
Use this as a prompt to try personalized AI activities for that individual.

---

## ⚙️ Settings

- **Facility Name** — appears on all printed documents and emails
- **Language** — UI language preference (multilingual in Enterprise)
- **Notifications** — birthday reminders and low-engagement alerts

---

## 💳 Subscription

Switch between Free, Pro, and Enterprise tiers.
Changes take effect immediately.

**Free → Pro upgrade:** All historical data is preserved. AI features unlock instantly.

---

## Tips from Expert Activity Directors

**Start every morning on the Dashboard.** The 60-second review tells you everything you need to know.

**Rate activities the same day.** Memory fades. Even a 30-second rating per resident makes your reports dramatically more valuable.

**Use personalized AI activities for disengaged residents.** If someone hasn't engaged in 3+ sessions, generate a personalized activity just for them.

**Print the calendar every Monday.** Post it in the activity room, nurses' station, and dining area. Residents look forward to seeing what's coming.

**Send family emails monthly.** Families who feel informed are happier. The emails take 2 minutes to send and build enormous goodwill.

**Check the Effectiveness Report monthly.** Retire low-scoring activities and generate fresh AI replacements.

---

## Need Help?

📧 support@activitypro.app
🌐 activitypro.app
