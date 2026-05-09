# 🐙 Pushing ActivityPro to GitHub — Step by Step

Follow these exact steps to get ActivityPro safely on GitHub with automatic backups.

---

## Step 1 — Create a GitHub Account (if needed)
Go to **github.com** → Sign Up → Free account

---

## Step 2 — Create a New Repository

1. Click the **+** button (top right) → **New repository**
2. Repository name: `activitypro`
3. Description: `AI-powered senior care activity calendar`
4. Set to **Private** (recommended — contains resident workflow code)
5. **Do NOT** check "Add README" (we already have one)
6. Click **Create repository**

---

## Step 3 — Open Terminal / Command Prompt

Navigate to your activitypro folder:

```bash
cd path/to/activitypro
# Example Windows: cd C:\Users\YourName\activitypro
# Example Mac:     cd ~/Documents/activitypro
```

---

## Step 4 — Initialize Git

```bash
git init
git add .
git status
```

You should see a list of files. Make sure `secrets.toml` is NOT listed
(it should show as ignored). If it appears, stop and check your `.gitignore`.

---

## Step 5 — First Commit

```bash
git commit -m "🌸 ActivityPro Phase 2 — Initial commit

- AI-powered activity calendar
- Resident management with 19 disability types
- Printable wall calendar and resident reports
- Family email notifications
- Staff daily reminders
- GitHub CI/CD pipeline
- Full documentation (SETUP, DEPLOYMENT, USER_GUIDE, CHANGELOG)"
```

---

## Step 6 — Connect to GitHub

Copy the URL from your GitHub repo page, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/activitypro.git
git branch -M main
git push -u origin main
```

GitHub will ask for your username and password.
**Use a Personal Access Token instead of your password:**
1. GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate new token → check `repo` scope → copy the token
3. Paste it as your password when git asks

---

## Step 7 — Verify It Worked

Go to `github.com/YOUR_USERNAME/activitypro`
You should see all your files and the beautiful README.

Click the **Actions** tab — your CI pipeline will run automatically!
Green checkmark = everything is good. ✅

---

## Future Updates — How to Push Changes

Every time you make changes:

```bash
git add .
git commit -m "Description of what changed"
git push
```

That's it! GitHub keeps every version — you can always roll back.

---

## Setting Up Branches (Recommended)

```bash
# Create a development branch for testing changes
git checkout -b develop

# Work on changes, then push to develop (safe — doesn't affect main)
git push origin develop

# When ready, merge to main
git checkout main
git merge develop
git push origin main
```

This way `main` is always your stable, working version.

---

## Connecting to Streamlit Cloud (Go Live!)

Once pushed to GitHub, see **docs/DEPLOYMENT.md** to deploy ActivityPro
as a live web app accessible from any phone or computer worldwide.
Takes about 10 minutes and it's free.

---

Need help? 📧 support@activitypro.app
