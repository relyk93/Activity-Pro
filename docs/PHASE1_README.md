# ActivityPro — Phase 1 Complete

> Foundation build: everything needed for a working, usable product.

---

## What Was Built

Phase 1 delivered a fully functional activity management app for senior living facilities, covering the entire core loop from scheduling activities to tracking resident engagement.

### Pages

| Page | What It Does |
|------|-------------|
| `dashboard.py` | Daily metrics, today's schedule, upcoming birthdays |
| `calendar_view.py` | Weekly calendar grid with clickable event details |
| `ai_generator.py` | Claude AI generates a full week of personalized activities |
| `residents.py` | Add/edit residents with disability profiles (19 types supported) |
| `rate_activities.py` | Log attendance, mood (1–5), and staff notes per session |
| `reports.py` | Engagement analytics and care plan summaries |
| `print_calendar.py` | Printable wall calendar and per-resident PDF reports |
| `notifications.py` | Email system for family updates and staff reminders |
| `settings.py` | Facility name, timezone, SMTP configuration |
| `subscription.py` | Tier management — Free, Pro ($29/mo), Enterprise ($79/mo) |

### Backend / Utils

| File | What It Does |
|------|-------------|
| `utils/database.py` | SQLite CRUD — residents, activities, scheduled events, engagements |
| `utils/auth.py` | Subscription gating and feature access control |
| `utils/email_sender.py` | SMTP client with HTML email templates |
| `utils/pdf_export.py` | Print-ready HTML generation for wall calendars and reports |

### Seed Data (auto-loaded on first run)

- **12 pre-built activities** — chair yoga, memory sharing, balloon volleyball, trivia, garden club, and more
- **8 sample residents** — realistic profiles with varied disability combinations

### Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Streamlit 1.32+ |
| Language | Python 3.9+ |
| Database | SQLite (cloud-ready schema) |
| AI | Claude API (Anthropic) — `claude-sonnet-4-5` |
| Email | SMTP (Gmail-compatible) |
| Export | HTML-to-print (browser rendering) |
| CI/CD | GitHub Actions |

### Subscription Tiers

**Free** — Calendar, 15 residents, basic tracking

**Pro ($29/mo)** — AI generation, mood tracking, care plans, printable calendars, email notifications, 19 disability types

**Enterprise ($79/mo)** — Multi-facility, multilingual, HIPAA-compliant cloud backup, priority support

---

## Known Limitations Going into Phase 2

- No staff login system — single shared account per facility
- No photo documentation for sessions
- Mood data exists but no trend visualization over time
- PDF export uses HTML-to-print (browser-dependent), not a true PDF library
- No integration with facility EHR systems (PointClickCare, MatrixCare)
- Subscription tier is hardcoded to "Pro" in seed data (no real billing)

---

## Files Delivered

```
activitypro/
├── app.py
├── requirements.txt
├── pages/ (10 pages)
├── utils/ (4 modules)
├── docs/ (5 documentation files)
├── .streamlit/config.toml
├── .streamlit/secrets.toml.template
├── .github/workflows/ci.yml
└── .gitignore
```

Total: **28 files, ~4,000 lines of code**
