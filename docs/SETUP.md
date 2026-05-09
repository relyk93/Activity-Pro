# 🛠 ActivityPro — Setup Guide

This guide walks you through getting ActivityPro running on your local machine from scratch.

---

## Prerequisites

| Requirement | Version | Check |
|------------|---------|-------|
| Python | 3.9 or newer | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| Anthropic API Key | — | platform.anthropic.com |

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/activitypro.git
cd activitypro
```

---

## Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed:**
- `streamlit` — the web UI framework
- `requests` — for Anthropic API calls

---

## Step 3 — Configure Secrets

Copy the template and fill in your values:

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
# Required for AI Generator
ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"

# Optional — for email notifications
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "yourname@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
FROM_EMAIL = "ActivityPro <yourname@gmail.com>"
```

**Getting your Anthropic API Key:**
1. Go to [platform.anthropic.com](https://platform.anthropic.com)
2. Sign in → API Keys → Create Key
3. Copy and paste into secrets.toml

**Gmail App Password (for email):**
1. Enable 2-Factor Auth on your Google account
2. Go to `myaccount.google.com → Security → App Passwords`
3. Create one for "Mail" and paste it as `SMTP_PASSWORD`

> ⚠️ **NEVER commit secrets.toml to GitHub.** It's already in `.gitignore`.

---

## Step 4 — Run the App

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

---

## Step 5 — First Time Setup

When you first open ActivityPro:

1. The database is **auto-created** with sample residents and activities
2. You start in **Pro tier** (for evaluation — change in Subscription page)
3. Go to **Settings** to set your facility name
4. Visit **AI Generator** to create your first weekly calendar
5. Add your real residents in **Residents** page

---

## Viewing on Your Phone (Same WiFi)

```bash
# Find your computer's IP
ipconfig          # Windows
ifconfig          # Mac/Linux

# Run with network access
streamlit run app.py --server.address 0.0.0.0

# Open on phone: http://YOUR-IP:8501
```

---

## Viewing Remotely (ngrok)

```bash
# Install ngrok from ngrok.com/download
# Then in a second terminal:
ngrok http 8501
# Copy the https://xxxx.ngrok.io URL — share with anyone
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'streamlit'`**
```bash
pip install streamlit
```

**App opens but AI Generator doesn't work**
- Check your `ANTHROPIC_API_KEY` in secrets.toml
- Make sure there are no spaces around the `=` sign

**Database errors**
```bash
# Delete and recreate the database
rm activitypro.db
python -c "from utils.database import init_db; init_db()"
```

**Email not sending**
- Make sure you're using a Gmail App Password (not your regular password)
- Check that 2FA is enabled on Gmail
- Verify SMTP settings in secrets.toml

---

## Next Steps
- [Deploy to Streamlit Cloud](DEPLOYMENT.md) — get a public URL
- [User Guide](USER_GUIDE.md) — learn all features
- [Changelog](CHANGELOG.md) — see what's new
