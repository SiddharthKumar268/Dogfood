# Doogfood Hackathon Portal (Dogfood 2026)

Full-stack Hackathon Management & Judging Portal built to satisfy the official **Dogfood 2026 Build Guide (v2)** specification.

- **Stack:** Python 3 + Flask + PyMongo + MongoDB + Server-Side Jinja2 (HTML5 / CSS3 / Vanilla JS).
- **Frontend Architecture:** **Zero React / No npm build pipeline.** All pages render server-side via Jinja2 so content (like project gallery titles) is immediately available in the raw HTML response for acceptance testing and indexing without JavaScript execution.
- **Tiers Completed:** **T1 (Core Portal & Gallery)** and **T2 (Judging Engine & Z-Score Normalization)** — 100% verified against the official acceptance checker `run.py`.

---

## 🚀 Quick Start (Native Execution - No Docker Needed)

Because MongoDB is running as a local service on Windows:

1. **Install requirements:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Start the Portal:**
   ```bash
   cd backend
   python avi.py
   ```
   *The portal automatically checks MongoDB on boot and auto-seeds fixture data from `fixtures.json` if empty.*

3. **Open the Portal:**
   Navigate to [http://localhost:8088](http://localhost:8088) in your browser.

---

## 🐳 Docker Deployment (Optional / Standard One-Command Rule)

If running in a Docker environment:
```bash
docker compose up
```
This starts both the `app` container and `db` (MongoDB 7) container.

---

## 🧪 Acceptance Checker (`run.py`)

Run the acceptance suite directly against the running portal:
```bash
python run.py .dogfood.toml
```

Output is recorded in `acceptance-report.txt`:
```
==================================================
      DOGFOOD 2026 ACCEPTANCE CHECKER REPORT     
==================================================
Target Portal: http://localhost:8088

[TIER 1 CHECKS]
  [PASS] T1.1: GET gallery (no auth) -> Expected: 200, Got: 200
  [PASS] T1.2: Gallery body contains 'HackTrack Pro' -> Found: True
  [PASS] T1.3: POST submit (participant, event closed) -> Expected: 4xx, Got: 403

[TIER 2 CHECKS]
  [PASS] T2.1: GET judge_scores as judge_a -> Expected: 200, Got: 200
  [PASS] T2.2: GET peer_scores as judge_b (isolation) -> Expected: 401/403, Got: 403
  [PASS] T2.3: GET judge_scores as participant -> Expected: 401/403, Got: 403
  [PASS] T2.4: GET csv_export as organizer -> Expected: 200 with CSV, Got: 200 (comma: True)

==================================================
                    SUMMARY                       
==================================================
Total Checks: 7/7 PASSED
Tier 1 (Core):     VERIFIED
Tier 2 (Judging):  VERIFIED
==================================================
ALL 7 ACCEPTANCE CHECKS PASSED SUCCESSFULLY!
```

You can also run the unit test suite:
```bash
python tests/test_acceptance.py
# or
python -m unittest discover tests
```

---

## 🔑 Pre-Seeded Test Accounts & Tokens

| Role | Email | Password | Pre-seeded Session Cookie |
|---|---|---|---|
| **Organizer** | `organizer@dogfood.dev` | `org123` | `session=org_7f2a` |
| **Judge Alpha** | `judge_a@dogfood.dev` | `judge123` | `session=jdg_a_91bc` |
| **Judge Beta** | `judge_b@dogfood.dev` | `judge456` | `session=jdg_b_44de` |
| **Participant Pat** | `participant@dogfood.dev` | `part123` | `session=prt_2e88` |
| **Participant Quinn** | `participant2@dogfood.dev` | `part456` | *(login via web form)* |

---

## 🌐 Routes & Role Permissions

| Route | Method | Access / Role | Description |
|---|---|---|---|
| `/` | GET | Public | Home / Welcome page |
| `/projects` | GET | Public (No auth) | Project Gallery with server-rendered titles |
| `/projects/new` | GET/POST | Participant | Submission form; rejects with `403` if deadline passed |
| `/login` | GET/POST | Public | Session authentication endpoint |
| `/dashboard` | GET | Authenticated | Role-aware dashboard (Participant, Judge, Organizer) |
| `/results` | GET | Public (Published) | Final ranked standings (403 until published) |
| `/api/judge/scores` | GET | Judge / Organizer | Returns judge's own scores; 403 for peer scores |
| `/api/judge/scores` | POST | Judge | Submit raw criteria scores |
| `/api/judge/assignments` | POST | Organizer / Admin | Batch round-robin judge assignment |
| `/api/judge/normalize` | POST | Organizer / Admin | Compute per-judge z-scores (handles stddev=0) |
| `/api/judge/publish` | POST | Organizer / Admin | Publishes final results to public gallery |
| `/api/export.csv` | GET | Organizer / Admin | Exports CSV report with rank, averages, judge counts |

---

## 🛡️ Critical Role Isolation (Check #5)

In compliance with Disqualification Gate #05, score privacy is enforced **strictly in the backend**:
- When a judge hits `/api/judge/scores?judge=judge_a` while logged in as `judge_b`, the backend extracts the session from the cookie, resolves the user, checks that `requestedJudgeId !== req.user.id`, and aborts with HTTP **403 Forbidden**.
- Participants hitting `/api/judge/scores` receive **403 Forbidden**.
- Unauthenticated requests receive **401 Unauthorized**.

---

## ⚖️ Judging Engine & Normalization (JUDGING.md)

1. **Raw Score:**
   $$\text{rawTotal} = \sum (\text{criterion.score} \times \text{criterion.weight})$$
2. **Per-Judge Z-Score:**
   $$\text{normalizedTotal} = \frac{\text{rawTotal} - \mu_j}{\sigma_j}$$
   - *Guard against uniform scoring:* If $\sigma_j = 0$ (e.g. Judge Beta gives all 5s), the divisor falls back to $1.0$, rendering the judge's score delta neutral ($0.0$) rather than crashing with division by zero.
   - *Incomplete review batches:* Only completed scores are averaged; unscored assignments never penalize projects as zero.

---

## ⚠️ Honest Limitations

1. **Fixed Session Lifetime:** Pre-seeded session tokens are static to guarantee acceptance checker determinism. In production, tokens would be rotated with rolling expirations.
2. **Local Email Verification:** User accounts are activated upon seed/registration without an external SMTP dependency.
3. **Rate Limiting:** Not enabled by default to ensure rapid-fire checker scripts run without synthetic throttling.

---

## 📜 License

[MIT License](LICENSE) © 2026 Doogfood Contributors.
