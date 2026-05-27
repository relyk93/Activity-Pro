# ActivityPro — Senior Care Calendar

## What It Is

ActivityPro is an all-in-one activity management platform built specifically for senior living facilities. It replaces paper schedules, spreadsheets, and fragmented tools with a single web app that handles planning, documentation, communication, and compliance — all in one place.

The app is built on Streamlit and powered by Claude AI (Anthropic). It runs in a browser, requires no installation, and is designed to be used daily by activity directors and floor staff.

---

## Who It Is For

- **Activity Directors** — plan calendars, generate AI-powered schedules, track resident engagement, run reports, manage staff, and communicate with families
- **Floor Staff** — view daily schedules, log engagement, rate activities, and access resident quick cards
- **Families** — receive personalised update emails with photos and engagement summaries

---

## What It Does Today

### Planning
- **AI Weekly & Monthly Calendar Generator** — generates a full activity schedule using Claude AI, personalised to your residents' real interests, past ratings, disabilities, and budget. Generates 6 activities per day (5 active + 1 wind-down). Supports day-of-week selection so solo staff can generate only for the days they work.
- **Day Selector** — choose exactly which days to generate (e.g. Friday + Saturday only for a solo shift)
- **Activity Library** — save, browse, and reuse activities across weeks
- **Single Activity Generator** — generate one custom activity for a specific resident or group

### Supply Management
- **Supply List Export** — after generating a calendar, view all supplies needed by day and as a consolidated shopping list. Download as CSV or printable PDF. Available from both the AI Generator and the Calendar page for the current week or full month.

### Resident Care
- **Resident Quick Cards** — at-a-glance profile for every resident: conditions, cognitive status, dietary needs, interests, staff notes, mood trend, engagement rate, and recent session history
- **AI Profile Generator** — one click generates a realistic sample profile for any resident using Claude AI
- **Engagement Tracking** — log whether each resident engaged with each activity, their mood before/after, and staff notes
- **At-Risk Alerts** — automatic flags for residents who haven't engaged in 14+ days or show declining mood

### Communication
- **Family Updates** — send personalised email updates to families with activity highlights, engagement summary, and photo attachments
- **Staff Daily Reminder** — email today's schedule to your team each morning
- **Pre-Brief** — morning briefing sheet for staff to review before the day starts

### Reporting & Compliance
- **Reports** — engagement rates, activity category breakdowns, resident participation trends, exportable for compliance documentation
- **Rate Activities** — staff rate each session so the AI learns what works for your residents
- **Print & Export** — print-ready calendar and activity sheets

### Stories
- **Story Generator** — AI writes personalised stories for individual residents or the whole group (reminiscence, adventure, holiday, and more). Printable as keepsakes or used as read-aloud group activities.

### Administration
- **Staff Management** — director creates staff accounts, assigns roles (director / floor staff)
- **Subscription Tiers** — Free, Pro (AI features + reports), and Enterprise
- **Dark / Light Mode** — theme toggle with persistent preference
- **Resident Council** — document and track resident council meetings and action items

---

## Why It Matters

Senior living facilities are chronically understaffed. Activity directors often work alone or with minimal support, responsible for planning and running 6+ activities per day, 5–7 days a week, while also documenting participation for licensing and compliance.

Most facilities still use paper schedules, printed supply lists, and manual family phone calls. ActivityPro removes all of that friction.

**The AI layer is the key differentiator.** Instead of searching the internet for activity ideas or guessing what residents will enjoy, the AI generator reads your residents' actual profiles — their conditions, mobility, cognitive status, dietary needs, and specific hobbies — and produces a full week or month of personalised, evidence-based activities in seconds. It learns from your ratings over time, stopping itself from suggesting activities that didn't land and repeating the ones residents loved.

---

## Potential & Roadmap

**Near-term (before go-live):**
- SMTP email (family updates and staff reminders)
- Stripe subscription payments (Pro/Enterprise upgrades)
- Persistent database (PostgreSQL) so data survives redeployments
- Real resident data replacing demo content

**Growth features:**
- PointClickCare / MatrixCare EHR integration (exporters already stubbed)
- Mobile-optimised view for floor staff on phones or tablets
- Resident family portal (families log in to view updates directly)
- Automated weekly family email digests
- Bulk resident import from CSV
- Offline mode for facilities with unreliable internet
- Multi-facility support (enterprise accounts manage multiple locations)
- Voice-to-text staff notes
- Activity outcome analytics tied to resident wellness metrics

**Market opportunity:**
There are over 30,000 assisted living facilities in the United States alone, most with no dedicated activity software. Existing tools (Activity Connection, Eldermark) are expensive, outdated, and desktop-only. ActivityPro is cloud-native, AI-first, and affordable — built to work for a solo activity director running a 40-bed memory care unit just as well as a 300-bed continuing care campus.

---

## Technical Stack

- **Frontend / App:** Streamlit (Python)
- **AI:** Claude Sonnet / Haiku (Anthropic API)
- **Database:** SQLite (demo) → PostgreSQL (production)
- **Email:** SMTP (Gmail or custom)
- **Payments:** Stripe
- **Deployment:** Streamlit Cloud (GitHub auto-deploy)
- **Image generation:** DALL-E 3 (OpenAI, optional)
