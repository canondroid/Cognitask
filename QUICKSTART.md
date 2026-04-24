# Quick Start

## Prerequisites

- Python 3.9 or later
- Node.js 18 or later + npm

---

## First-Time Setup

```bash
# Install Python dependencies
pip install flask flask-cors bcrypt numpy pandas scikit-learn

# Install frontend dependencies
cd frontend && npm install && cd ..
```

---

## Running Locally

You need two terminals open at the same time.

**Terminal 1 — Backend**
```bash
python webui.py
# → Running on http://127.0.0.1:5001
```

**Terminal 2 — Frontend**
```bash
cd frontend && npm run dev
# → http://localhost:5173
```

Open `http://localhost:5173`. Vite proxies `/api/*` to port 5001 so session cookies work correctly.

To stop: press `Ctrl+C` in each terminal.

---

## New User Flow

1. **Register** — create a username and password
2. **Onboarding survey** — 3 questions about your schedule and planning tendency; sets your starting cognitive limit so the system is useful from day 1
3. **Dashboard** — add tasks, click "Analyse Plan", see your cognitive load score, ML risk (after 15 days), and any nudges
4. **End of day** — record how it actually went (completion rate); this feeds the EMA and retrains the ML model

---

## Mental Effort Levels

Pick the level that matches how the task *feels*, not how long it takes.

| Level | Examples | Feeling |
|---|---|---|
| LOW | Email, admin, routine meetings | Autopilot — not draining |
| MEDIUM | Code review, writing, planning | Focused but manageable |
| HIGH | System design, complex debugging, research | Intensive — need breaks after |

---

## Understanding Your Plan Result

```
daily_load      — total cognitive load score for the day
current_limit   — your EMA-learned capacity
ml_risk_score   — overload probability 0–1 (null until 15 days of history)
should_nudge    — whether the system is warning you
nudge_severity  — "caution" or "warning"
user_state      — "new" (<5 days) | "learning" (<15) | "established" (15+)
```

---

## Recording Outcomes

At the end of the day, set your completion rate — what fraction of the planned tasks did you actually finish?

| Rate | Meaning |
|---|---|
| 1.0 | Finished everything |
| 0.7–0.9 | Got most things done |
| 0.5–0.7 | Struggled, about half done |
| < 0.5 | Overloaded |

**When does recording change your capacity limit?**
Only on *surprising* outcomes:
- Planned above limit + completed ≥ 70% → limit rises (genuine growth)
- Planned below limit + completed < 70% → limit falls (true underperformance)
- Planned above limit + failed → no change (expected — you were already warned)
- Planned below limit + succeeded → no change (expected — you were within capacity)

---

## FAQ

**Q: Why isn't the ML model giving predictions?**
You need at least 15 recorded days. Keep recording outcomes each day.

**Q: Can I skip the onboarding survey?**
Yes — there's a "Skip for now" option. Your first recorded outcome will seed the limit instead; onboarding just gives you a better starting point immediately.

**Q: What if I disagree with a nudge?**
Override it. The system records your actual completion rate and learns from that, not from whether you followed the advice.

**Q: How do I reset a user's data?**
Delete `data/{username}.json` and `data/{username}_model.pkl`. The next login starts fresh.

---

## Troubleshooting

**"ML risk is always null"**
Need 15+ days of history. Check `days_recorded` in the `/api/status` response.

**"Port already in use" on macOS**
AirPlay Receiver occupies port 5000. This app runs on 5001 — if it still conflicts, go to System Settings → General → AirDrop & Handoff and disable AirPlay Receiver.

**Two users on the same device**
Flask sessions are browser cookies. Two people using the same browser profile will share a session. Each test user should use their own device or a separate browser profile.
