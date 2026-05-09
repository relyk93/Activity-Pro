# 🌸 ActivityPro — Senior Care Activity Calendar

> **AI-powered activity management for senior living facilities — designed by activity directors, for activity directors.**

[![CI Status](https://github.com/YOUR_USERNAME/activitypro/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/activitypro/actions)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Phase Roadmap](#phase-roadmap)
- [Documentation](#documentation)

---

## ✨ Features

### Free Tier
- Weekly activity calendar with clickable event details
- 12+ pre-loaded expert-designed activities with full instructions
- Up to 15 residents with disability profiles
- Basic engagement tracking

### Pro Tier ($29/month)
- AI-generated weekly calendars via Claude
- Disability-aware personalized activities per resident
- Mood tracking before and after each session
- Care plan summaries and engagement reports
- Printable wall calendars and resident PDF reports
- Family email updates and daily staff reminders
- Birthday awareness and 19 disability types supported

### Enterprise Tier ($79/month)
- Multi-facility management
- Multilingual support
- HIPAA-compliant cloud backup
- Priority support and onboarding

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/activitypro.git
cd activitypro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml with your Anthropic API key

# 4. Run
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

See [docs/SETUP.md](docs/SETUP.md) for full setup and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) to deploy online.

---

## Project Structure

```
activitypro/
├── app.py                     # Main app + navigation + global CSS
├── requirements.txt
├── README.md
├── pages/
│   ├── dashboard.py           # Home dashboard
│   ├── calendar_view.py       # Weekly calendar grid
│   ├── ai_generator.py        # AI activity generator
│   ├── residents.py           # Resident management
│   ├── rate_activities.py     # Engagement tracking
│   ├── reports.py             # Analytics + care plans
│   ├── print_calendar.py      # Printable calendar + reports
│   ├── notifications.py       # Email notifications
│   ├── settings.py
│   └── subscription.py
├── utils/
│   ├── database.py            # SQLite (cloud-ready)
│   ├── auth.py
│   ├── email_sender.py        # SMTP + HTML email templates
│   └── pdf_export.py          # Print-ready HTML generation
├── docs/
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   ├── USER_GUIDE.md
│   └── CHANGELOG.md
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.template
└── .github/workflows/ci.yml
```

---

## Phase Roadmap

**Phase 1 — Core (Complete):** AI calendar, residents, engagement, reports, subscriptions

**Phase 2 — Polish (Complete):** Mobile UI, printable calendar, email notifications, GitHub CI, full docs

**Phase 3 — Power Features:** Staff logins, photo documentation, EHR integration, trend graphs

**Phase 4 — Scale:** Stripe payments, multi-facility, multilingual, native mobile app

---

## Documentation
| File | Description |
|------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Local setup guide |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deploy to web |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Feature walkthrough |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |

---

Built with 💚 for activity directors worldwide · activitypro.app
