# ActivityPro — Director Setup Checklist

> This document lists every piece of demo, placeholder, or experimental data currently in the app.
> Work through this checklist before presenting to a real facility or going live.

---

## 🔴 Critical — Do Before Any Presentation

### 1. API Key Security
The Anthropic API key in `.streamlit/secrets.toml` was shared in chat and should be replaced.

- [ ] Go to [console.anthropic.com](https://console.anthropic.com) → API Keys
- [ ] Disable the current key
- [ ] Create a new key and paste it into `.streamlit/secrets.toml`

```toml
ANTHROPIC_API_KEY = "sk-ant-your-new-key-here"
```

---

## 🟠 High Priority — Replace Before Showing Anyone

### 2. Facility Name
Currently hardcoded as **"Sunrise Senior Living"** in the database seed.

**How to change it:** Log in as director → Settings → Facility & Display → update the facility name field.

> After changing it once in Settings, it updates everywhere in the app.

---

### 3. Demo Staff Accounts
Two placeholder accounts are seeded on first launch. These are shown on the login screen.

| Username | Password | Role |
|----------|----------|------|
| `director` | `ActivityPro2024!` | Director |
| `staff1` | `Staff2024!` | Floor Staff |

**How to replace them:**
- [ ] Log in as `director`
- [ ] Go to **Staff Management**
- [ ] Add your real staff accounts with real names and passwords
- [ ] Deactivate `director` and `staff1` once you have your own director account
- [ ] If doing a demo, keep them but note they are for demo purposes only

---

### 4. Demo Residents
Eight fictional residents are pre-loaded. They have fake names, rooms, birthdays, and medical notes.

| Name | Room | Notes |
|------|------|-------|
| Margaret Thompson | 101 | Arthritis, loves gardening |
| Robert 'Bob' Jenkins | 102 | Hearing loss, diabetic |
| Dorothy Alvarez | 103 | Dementia, limited mobility |
| Harold Kim | 104 | Vision impairment, vegetarian |
| Evelyn Moore | 105 | Anxiety, arthritis |
| Frank Deluca | 106 | Parkinson's |
| Grace Washington | 107 | No disabilities noted |
| Walter Nguyen | 108 | Dementia, wheelchair |

**For a real facility:**
- [ ] Go to **Residents** → delete each demo resident
- [ ] Add your real residents with accurate profiles
- [ ] Add family contact emails so Family Updates work

**For demo/presentation:** Leave them in — they show off the system well and the data is realistic.

---

### 5. Demo Calendar Events & Engagement History
Two weeks of fake sessions and engagement scores are seeded automatically to make the dashboard, reports, and charts look populated.

- 23 calendar events spanning past two weeks + this week
- Mood scores, engagement rates, and staff notes for all 8 demo residents
- Walter Nguyen is intentionally seeded as "at-risk" (low engagement) to show the alert system

**For a real facility:**
- [ ] Delete the demo events from the Calendar page
- [ ] The real engagement data will build up naturally as you use the app

**For demo/presentation:** Leave them — they demonstrate the Reports, Dashboard alerts, and Mood Trends features.

---

## 🟡 Medium Priority — Update Before Going Live

### 6. Email / SMTP Configuration
Family Updates and Notifications cannot send emails until SMTP is configured.

- [ ] Open `.streamlit/secrets.toml`
- [ ] Fill in your email provider's settings:

```toml
SMTP_HOST     = "smtp.gmail.com"       # or your provider
SMTP_PORT     = 587
SMTP_USER     = "you@yourfacility.com"
SMTP_PASSWORD = "your-app-password"
FROM_EMAIL    = "you@yourfacility.com"
```

> For Gmail: use an App Password (not your main password). Go to Google Account → Security → 2-Step Verification → App Passwords.

---

### 7. Stripe Payment Configuration
The Professional plan upgrade button is disabled until Stripe is configured.

- [ ] Create a [Stripe](https://dashboard.stripe.com) account
- [ ] Products → Add Product → "ActivityPro Professional" → $49/month recurring
- [ ] Copy the `price_xxx` ID from the product page
- [ ] Get your API keys from Developers → API Keys
- [ ] Add to `.streamlit/secrets.toml`:

```toml
STRIPE_SECRET_KEY      = "sk_live_..."
STRIPE_PUBLISHABLE_KEY = "pk_live_..."
STRIPE_PRICE_ID        = "price_..."
APP_URL                = "https://your-app.streamlit.app"
```

> Start with test keys (`sk_test_...`) so you can test the checkout flow without real charges.

---

### 8. Contact Email Throughout the App
`kyl3rking@gmail.com` appears in the following places and should be replaced with your organization's official contact:

| Location | What It's Used For |
|----------|--------------------|
| `index.html` — nav, hero, pricing, footer | All landing page CTAs and contact links |
| `pages/subscription.py` — footer | Support contact in the subscription page |
| `docs/ActivityPro_Pitch.html` | Pitch document contact info |

**For a presentation:** Fine to leave as-is since this is your contact.
**For a white-label or partner deployment:** Replace with the facility/partner email.

---

### 9. EHR Integration Credentials
The EHR integration framework is built but not connected to a real system.

- [ ] Go to **Settings → EHR Integration**
- [ ] Select your provider (PointClickCare or MatrixCare)
- [ ] Enter real credentials from your EHR vendor
- [ ] Or add them directly to `.streamlit/secrets.toml`:

```toml
[ehr]
pcc_client_id     = ""
pcc_client_secret = ""
pcc_org_uuid      = ""
pcc_sandbox       = true   # set false for production
mc_api_key        = ""
mc_base_url       = ""
```

---

## 🔵 Lower Priority — Polish for Production

### 10. Landing Page — Fictional Impact Stats
These numbers are illustrative. Replace with your real data before using the page to attract real customers.

| Stat | Current Value | What to Replace With |
|------|--------------|----------------------|
| Engagement rate | 94% | Your facility's actual rate from Reports |
| Mood improvement | +1.4 per session | Your actual mood before/after data |
| Planning time | 12 min | Time your director actually saves |
| Family calls | 0 calls | Your experience after using Family Updates |

**Location:** `index.html` — the teal gradient strip between Moments and Testimonials.

---

### 11. Landing Page — Fictional Testimonials
Three quotes from fictional people appear on the landing page. Replace with real testimonials once you have them, or reword to remove attribution.

| Name | Role |
|------|------|
| Sarah M. | Activity Director, Memory Care Facility |
| James T. | Son of a resident |
| Denise R. | Floor Staff, Assisted Living Community |

**Location:** `index.html` — Testimonials section.

---

### 12. Landing Page — Fictional Resident Moments
Four activity scene cards reference fictional residents (Dorothy, Bob, Margaret, Walter). These match the demo residents in the app and are fine for a demo presentation. For a live public landing page, replace with generic or real stories.

**Location:** `index.html` — Real Moments section.

---

### 13. Pitch Document — Date and Contact
The pitch document needs updating each time you present it.

- [ ] Open `docs/ActivityPro_Pitch.html` in a text editor
- [ ] Update the date from `May 2026` to the current presentation date
- [ ] Verify the contact email and pricing reflect your current offering
- [ ] Replace the `40%+` paperwork statistic with real industry data if presenting to a skeptical audience

---

### 14. Demo Credentials on Login Screen
The login page shows demo credentials in a styled box. This is great for demos but should be removed before giving real staff access.

**Location:** `pages/login.py` — the "✦ Live Demo Access" box at the bottom of the login form.

To remove it for production: delete lines 37–57 in `pages/login.py`.

---

### 15. Subscription Tier in Database
The demo is seeded with the `pro` tier and a resident limit of 999.

For a real free-tier launch:
- [ ] Change `'pro'` to `'free'` and `999` to `15` in `utils/database.py` line ~181
- [ ] Or delete `activitypro.db` to reseed from scratch on next launch

---

## 📋 Quick Reference — What's Real vs Demo

| Item | Status | Notes |
|------|--------|-------|
| 12 pre-built activities | ✅ Real | Professional, usable as-is |
| Activity instructions & supplies | ✅ Real | Evidence-based, ready to use |
| AI activity generator | ✅ Real | Works with your Anthropic key |
| Resident Council log | ✅ Real | Empty until you add meetings |
| Stripe checkout flow | ✅ Real | Needs your Stripe keys |
| EHR integration framework | ⚠️ Framework | Code is ready, needs your credentials |
| 8 demo residents | 🎭 Demo | Replace with real residents for production |
| Calendar events | 🎭 Demo | Seeded for demo purposes |
| Engagement/mood history | 🎭 Demo | Seeded for demo purposes |
| Staff accounts | 🎭 Demo | Replace with real accounts |
| Landing page testimonials | 🎭 Demo | Replace with real quotes |
| Impact stats (94%, +1.4) | 🎭 Demo | Replace with real facility data |
| Facility name | 🎭 Demo | Change in Settings |
| SMTP email | ❌ Not configured | Add to secrets.toml |
| Stripe payments | ❌ Not configured | Add keys to secrets.toml |
| EHR credentials | ❌ Not configured | Add to secrets.toml |

---

*Last updated: May 2026 — ActivityPro Phase 3*
