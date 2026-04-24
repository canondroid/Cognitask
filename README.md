# Cognitive Load-Aware Task Planning System

A hybrid HCI-ML system that learns each user's sustainable daily cognitive capacity and provides non-blocking nudges when a planned day risks overload.

---

## Core Philosophy

1. **Mental effort is user-defined** — users know their tasks; the system never overrides that judgment
2. **Time amplifies effort, never dominates it** — duration is a modifier, not the main factor
3. **ML supports decisions, it does not make them** — risk scores inform nudges; users always have the final word
4. **Capacity must be allowed to grow** — the EMA rises on genuine growth signals, not just falls on failure

---

## Architecture

```
webui.py  (Flask REST API, auth, per-user persistence)
    └── CognitiveTaskPlanner  (orchestrator — cognitive_task_planner.py)
            ├── CognitiveLoadCalculator   rule-based cost formula
            ├── CapacityLearner           EMA tracks sustainable daily load
            └── OverloadPredictor         Logistic Regression, activates at 15 days
```

### Decision Flow

```
User input (tasks + effort + duration)
    ↓
Rule-based cost:  Cost = Effort × (1 + α_eff × Duration/60)
Daily load     =  Σ(task costs)
    ↓
Capacity check:   compare to EMA-learned limit
    ↓
ML risk score:    P(overload | 6 features)   [only after 15 days]
    ↓
Nudge decision:   load > limit AND risk ≥ 0.6  →  warn
                  otherwise                    →  silent
    ↓
User sees result and decides
```

---

## Components

### CognitiveLoadCalculator (Rule-Based)

**Formula:** `Cost = Effort × (1 + α_eff × Duration / 60)`
where `α_eff = 0.10 × effort_value` — LOW=0.10, MEDIUM=0.20, HIGH=0.30

Higher-effort tasks accumulate fatigue faster with duration. The formula is fully transparent and deterministic.

### CapacityLearner (EMA)

Learns each user's sustainable daily load from recorded outcomes. Updates only on *surprising* results — expected outcomes carry no new information.

**Surprise filter (applied first):**
```
over_limit = planned_load > current_limit
success    = completion_rate >= 0.7

Skip if over_limit != success:
  planned above + failed   → expected failure   → no update
  planned below + succeeded → expected success  → no update

Update if over_limit == success:
  planned above + succeeded → genuine growth    → limit rises
  planned below + failed    → true underperform → limit falls
```

**EMA update (applied when outcome is surprising):**
```
observed = planned_load × completion_rate
distance_ratio = |observed − current_limit| / current_limit
effective_α = 0.3 × max(0.3, 1.0 − distance_ratio)   # trust less when far from belief
new_limit = effective_α × observed + (1 − effective_α) × current_limit
delta = clamp(new_limit − current_limit, −0.75, +0.75)  # cap single-day swing
current_limit += delta
```

**Anomaly guard:** skip the update entirely if `planned_load > current_limit × 2.0` (extreme crunch) or `< current_limit × 0.3` (rest/sick day). Applied before the surprise filter.

**Seeding:** onboarding survey sets the initial limit from day 0. If skipped, the first recorded outcome seeds it from `observed`.

**User states:**

| Days recorded | State | Behaviour |
|---|---|---|
| 0–4 | New | EMA active, no ML |
| 5–14 | Learning | EMA refining, ML not yet trained |
| 15+ | Established | EMA stable, ML predictions active |

### OverloadPredictor (Logistic Regression)

Activates after 15 recorded days. Outputs a risk probability (0–1) used only for nudge decisions — never for blocking.

**Features:**

| Feature | Role |
|---|---|
| `planned_load` | Raw cognitive load |
| `task_count` | Context-switching overhead |
| `high_effort_count` | Exhaustion factor |
| `has_deadline` | Stress factor |
| `day_of_week` | Weekly rhythm |
| `load_to_limit_ratio` | Personalised signal — most important |

**Why Logistic Regression:**

| Criterion | Logistic Regression | Deep Learning |
|---|---|---|
| Interpretability | High (coefficients) | None (black box) |
| Data needs | Low (15+ samples) | High (1000+) |
| Probabilistic output | Yes | Yes |
| Overfitting risk | Low (L2 regularisation) | High |
| Training time | < 1 second | Minutes–hours |

**Note on anomalous entries:** the EMA skips extreme outlier days (its anomaly guard), but the ML model trains on the full unfiltered history. A freak day that the EMA correctly ignores still influences the regression weights.

### Nudge Logic

```
if load > limit AND ml_risk >= 0.6:
    if ml_risk >= 0.8:  severity = "warning"
    else:               severity = "caution"
else if ml unavailable AND load / limit >= 1.5:
    severity = "warning"
else if ml unavailable AND load / limit >= 1.2:
    severity = "caution"
else:
    silent
```

---

## Data Persistence

No database — file-based only:

| File | Contents |
|---|---|
| `users.json` | bcrypt-hashed credentials |
| `data/{username}.json` | EMA state, history, today's plan |
| `data/{username}_model.pkl` | Trained scikit-learn model (after 15 days) |

On Railway, these files live on a mounted Volume at `/mnt/data`.

---

## API Endpoints

All routes are prefixed `/api`. Session-based auth (signed cookie, `SECRET_KEY` env var).

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/api/register` | — | Create account |
| POST | `/api/login` | — | Authenticate |
| POST | `/api/logout` | ✓ | Clear session |
| POST | `/api/onboarding` | ✓ | Set initial capacity from survey |
| POST | `/api/plan` | ✓ | Analyse a task list |
| POST | `/api/plan/commit` | ✓ | Commit today's plan |
| GET | `/api/plan/today` | ✓ | Fetch committed plan |
| POST | `/api/record` | ✓ | Record day outcome |
| GET | `/api/history` | ✓ | All recorded days |
| GET | `/api/status` | ✓ | User state + current limit |
| GET | `/api/usage-metrics` | ✓ | Engagement / overload metrics |
| GET | `/api/calibration-metrics` | ✓ | EMA convergence metrics |

---

## Deployment (Railway)

The app is configured for single-service deployment. Flask serves both the API and the built React frontend.

**Environment variables required:**

| Variable | Value |
|---|---|
| `SECRET_KEY` | Any long random string |
| `DATA_DIR` | `/mnt/data` (Railway Volume mount path) |

**Railway setup:**
1. Push repo to GitHub
2. New Railway project → deploy from GitHub
3. Add a Volume mounted at `/mnt/data`
4. Set the two env vars above
5. Railway builds frontend via `nixpacks.toml` (`npm run build`) then starts `python webui.py`

**Local development** — see [QUICKSTART.md](QUICKSTART.md).

---

## Expected Performance

| Metric | Value |
|---|---|
| ML accuracy (15–20 samples) | 70–80% |
| Task planning latency | < 100 ms |
| Outcome recording latency | < 50 ms |
| Model retraining time | < 1 second |

### Evaluation Criteria (User Study)

- Overload rate: target < 30% of recorded days
- Mean completion rate: target ≥ 0.75
- Engagement rate: committed plan days that also have a recorded outcome
- Dropout rate: fraction of study window days with no activity

---

## Frontend Pages

```
pages/
  Login.jsx, Register.jsx   — auth
  Onboarding.jsx            — cold-start survey
  Dashboard.jsx             — task entry, load display, nudges
  History.jsx               — past outcomes

components/
  TaskForm.jsx              — add/edit tasks
  PlanResult.jsx            — load score, risk, nudge message
  StatusBar.jsx             — nav header
  ui/                       — shadcn/ui primitives
```
