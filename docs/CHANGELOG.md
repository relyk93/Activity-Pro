# 📋 ActivityPro Changelog

All notable changes to ActivityPro are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] — Phase 2 Release

### Added
- **🖨️ Print & Export page** — landscape weekly wall calendar + portrait resident report, both download as browser-printable HTML
- **🔔 Notifications page** — family update emails with engagement stats and staff notes; daily staff schedule reminders; low engagement alerts
- **📧 Email system** (`utils/email_sender.py`) — SMTP via Gmail or any provider, beautiful HTML templates for family and staff emails
- **📄 PDF/Print export** (`utils/pdf_export.py`) — print-ready HTML generation for calendar and resident reports
- **📱 Mobile-responsive CSS** — touch-friendly buttons (44px minimum), readable text on phones, responsive sidebar
- **⚙️ Streamlit config** (`.streamlit/config.toml`) — custom theme matching ActivityPro brand colors, headless server config for deployment
- **🔐 Secrets template** (`.streamlit/secrets.toml.template`) — safe template for API keys and SMTP config
- **🤖 GitHub Actions CI** (`.github/workflows/ci.yml`) — automated syntax checking, database test, file verification, secrets protection check on every push
- **📚 Full documentation suite:**
  - `docs/SETUP.md` — local setup walkthrough
  - `docs/DEPLOYMENT.md` — Streamlit Cloud, ngrok, Railway, Render, custom domains
  - `docs/USER_GUIDE.md` — complete feature guide written for activity directors
  - `docs/CHANGELOG.md` — this file
- **`.gitignore`** — protects secrets, database, pycache, OS files

### Changed
- Navigation sidebar now includes Print & Export and Notifications pages
- App.py routing updated for new pages
- README.md completely rewritten with badges, feature table, project structure, roadmap

### Security
- secrets.toml confirmed in .gitignore — API keys and SMTP passwords never committed to GitHub
- GitHub Actions checks secrets protection on every push

---

## [1.0.0] — Phase 1 Release

### Added
- **🏠 Dashboard** — daily metrics, today's schedule, upcoming birthdays, engagement snapshot
- **📅 Calendar** — weekly grid view with clickable events, full activity details, step-by-step instructions, supply lists, accessibility notes
- **🤖 AI Generator** — weekly calendar generation, single activity generation, personalized activities per resident (Pro feature)
- **👥 Residents** — full roster management with 19 disability types, engagement history per resident
- **⭐ Rate Activities** — per-resident engagement tracking, mood before/after (1-5 scale), staff notes, activity ratings
- **📊 Reports** — individual resident reports with care plan summaries, monthly facility report, activity effectiveness ranking
- **⚙️ Settings** — facility name, language preference, notifications
- **💳 Subscription** — Free / Pro / Enterprise tier management
- **🗄️ Database** (`utils/database.py`) — SQLite with cloud-ready schema, full CRUD for residents, activities, events, engagements, subscription
- **🔐 Auth** (`utils/auth.py`) — subscription gating for Pro/Enterprise features
- **12 pre-loaded activities** — chair yoga, memory sharing, balloon volleyball, guided meditation, bingo, sensory bin, armchair travel, hand massage, watercolor art, trivia, morning stretch, tabletop gardening
- **8 sample residents** — with realistic disability profiles including dementia, Parkinson's, wheelchair use, hearing loss, vision impairment

---

## Upcoming — Phase 3

- Staff login accounts with role-based access (Director vs. Floor Staff)
- Photo documentation per activity session
- Clinical-grade PDF exports for care plan integration
- Trend graphs showing resident mood over time
- EHR system integration (PointClickCare, MatrixCare)

## Upcoming — Phase 4

- Stripe payment processing for real subscription billing
- Multi-facility management dashboard
- Full multilingual support (Spanish, French, Mandarin, Japanese, Portuguese)
- Native iOS and Android mobile app
- Partner program for senior living networks
