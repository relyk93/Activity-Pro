# Potential Upgrades & Deferred Features

Things that are technically possible but not implemented yet — either because they require paid API tiers, additional setup, or aren't needed for the current demo stage.

---

## 1. Extended Output Tokens (Claude API)

**What it unlocks:** Claude Sonnet currently has a hard cap of 8,192 output tokens per API call. This is why the calendar JSON schema was trimmed (removed `instructions`, `disability_friendly`, `interest_connection` fields) and descriptions capped to one sentence — to keep the 7-day × 6-activity response under the limit.

With extended output enabled, you could:
- Restore full `instructions` (step-by-step activity guide) to calendar-generated activities
- Restore `interest_connection` and `disability_friendly` tags
- Allow longer descriptions without parse errors
- Potentially generate 2 weeks at once instead of one

**How to enable:** Add the Anthropic extended-output beta header to the API request in `pages/ai_generator.py` inside `call_claude()`:

```python
headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "output-128k-2025-02-19",   # ← add this line
}
```

Then raise `max_tokens` on calendar calls (currently 8000) to something like `32000` or `64000`.

**Requires:** Confirm this beta header is available on your Anthropic account tier. Check the [Anthropic docs](https://docs.anthropic.com) for the current beta header name — it may have changed since this was written.

**Files to update:** `pages/ai_generator.py` → `call_claude()` headers dict, and both `call_claude(... max_tokens=8000)` calls in the calendar generation section of Tab 1.

---

## 2. DALL-E Image Generation

Already wired up for Single Activity (Tab 2) and Personalized Activities (Tab 3). Requires `OPENAI_API_KEY` in Streamlit secrets. Not enabled for the calendar generator to avoid cost at scale.

---

## 3. PostgreSQL / Supabase (Persistent Database)

SQLite resets on every Streamlit Cloud redeploy. See `BEFORE_GO_LIVE.md` for migration notes.

---

## 4. PointClickCare / MatrixCare EHR Export

Stubs exist in the codebase. Full integration requires facility-level API credentials from the EHR vendor.
