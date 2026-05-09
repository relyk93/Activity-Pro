# 🚀 ActivityPro — Deployment Guide

Get ActivityPro online with a real URL — accessible from any phone, tablet, or computer worldwide.

---

## Option 1 — Streamlit Cloud (Recommended · Free)

The easiest way to deploy ActivityPro publicly. Takes about 10 minutes.

### Step 1 — Push to GitHub

```bash
cd activitypro

# Initialize git (if not done yet)
git init
git add .
git commit -m "Initial commit — ActivityPro Phase 2"

# Create repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/activitypro.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository: `YOUR_USERNAME/activitypro`
5. Main file path: `app.py`
6. Click **Deploy**

### Step 3 — Add Secrets

In the Streamlit Cloud dashboard:
1. Go to your app → **Settings → Secrets**
2. Paste your secrets (same as secrets.toml):

```toml
ANTHROPIC_API_KEY = "sk-ant-your-key"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "yourname@gmail.com"
SMTP_PASSWORD = "your-app-password"
FROM_EMAIL = "ActivityPro <yourname@gmail.com>"
```

3. Click **Save** — your app restarts with secrets active

Your app is now live at:
```
https://YOUR_USERNAME-activitypro-app-XXXXX.streamlit.app
```

Share this URL with any staff member worldwide — no install needed!

---

## Option 2 — ngrok (Quick Remote Access)

Best for temporary sharing or testing from your phone while the app runs locally.

```bash
# 1. Download ngrok from ngrok.com/download
# 2. Run your app
streamlit run app.py

# 3. In a second terminal
ngrok http 8501
```

You get a URL like `https://abc123.ngrok.io` — valid while ngrok is running.

---

## Option 3 — Railway / Render (More Control)

For teams that want more server control or custom domains.

### Railway

```bash
# Install Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

### Render

1. Create account at render.com
2. New → Web Service → Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add environment variables (same as secrets.toml)

---

## Custom Domain (Optional)

Once deployed to Streamlit Cloud or Render:

1. Buy a domain (e.g., `activitypro.yourfacility.com`) from Namecheap or GoDaddy (~$12/year)
2. Add a CNAME record pointing to your Streamlit/Render URL
3. Configure in your hosting dashboard

---

## Database in Production

The current SQLite database works great for single-facility use on Streamlit Cloud.

**Important:** Streamlit Cloud resets the filesystem on each redeploy. To persist data:

**Option A — Keep SQLite (Simple)**
- Export your data regularly from the Reports page
- Re-import if needed after redeployment

**Option B — Migrate to Supabase (Recommended for Production)**
1. Create free account at supabase.com
2. Get your connection string
3. Add to secrets.toml: `DATABASE_URL = "postgresql://..."`
4. Update `utils/database.py` to use psycopg2 instead of sqlite3
   - All queries are standard SQL — migration is straightforward

**Option C — PlanetScale (MySQL)**
Similar to Supabase but MySQL-based.

---

## GitHub Actions CI

The `.github/workflows/ci.yml` pipeline automatically runs on every push:
- Syntax checking all Python files
- Database initialization test
- File existence verification
- Secrets protection check

**Setting up GitHub Actions:**
1. Push to GitHub (done above)
2. Go to your repo → **Actions** tab
3. CI runs automatically on every push to `main` or `develop`

**Adding status badge to README:**
Replace `YOUR_USERNAME` in the README badge URL with your actual GitHub username.

---

## Production Checklist

Before going live with real resident data:

- [ ] Secrets.toml is in .gitignore ✅ (already done)
- [ ] API key is set in Streamlit Cloud secrets
- [ ] Facility name set in Settings page
- [ ] Test email by sending a staff reminder
- [ ] All real residents added and disability profiles complete
- [ ] First AI-generated calendar reviewed and approved
- [ ] Staff trained using USER_GUIDE.md
- [ ] Database backup strategy decided (see above)

---

## Support

Having trouble deploying? Check [docs/SETUP.md](SETUP.md) first, then:
- 📧 support@activitypro.app
- 🌐 activitypro.app/docs
