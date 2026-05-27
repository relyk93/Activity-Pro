# Before Go-Live Checklist

Things that are NOT needed for demo but must be done before a real facility uses the app.

---

## 1. SMTP — Email Sending
Family update emails and staff daily reminders are wired up but won't send until SMTP is configured.

In Streamlit Cloud → your app → Settings → Secrets, add:
```toml
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "you@gmail.com"
SMTP_PASSWORD = "your-16-char-app-password"
FROM_EMAIL    = "you@gmail.com"
```
For Gmail, use an App Password (not your real password):
https://myaccount.google.com/apppasswords

---

## 2. Stripe — Pro Subscription Upgrades
The upgrade flow is built but inactive without live Stripe keys.

In Streamlit Cloud → Secrets, add:
```toml
STRIPE_SECRET_KEY      = "sk_live_..."
STRIPE_PUBLISHABLE_KEY = "pk_live_..."
STRIPE_WEBHOOK_SECRET  = "whsec_..."
STRIPE_PRO_PRICE_ID    = "price_..."
```

---

## 3. Anthropic API Key (needed for AI features)
AI Generator, Story Generator, and Resident Card AI profiles all require this.
Already needed for demo if you want to show AI features.

In Streamlit Cloud → Secrets:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## 4. Replace Demo Data with Real Residents
Remove any test/sample residents and add actual facility residents before real use.

---

## 5. Compliance / Facility Review
- Confirm data storage meets your facility's privacy requirements
- SQLite DB is stored on Streamlit Cloud's ephemeral filesystem — data resets on redeploy
- For production, migrate database to a persistent store (PostgreSQL, Supabase, etc.)
