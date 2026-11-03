# ⚖️ SchemaCourt

> **The Change Review Room for Data Contracts**  
> *Built with Switch AI, DuckDB, Claude Code, and Streamlit*  
> *Submitted to the **Flip the Switch Hackathon** (Nov 4–7, 2026)*

---

## 🎯 The Pitch

When an upstream microservice changes an event payload, the backend team considers it a safe enhancement. Meanwhile, downstream analytical SQL models silently evaluate missing columns to `NULL`, breaking executive revenue reporting.

**SchemaCourt brings the backend producer (`@alex_backend`), the data owner (`@maya_data`), and an autonomous AI engineer (`@claude`) into a shared Switch Room to:**
1. **Detect & Investigate:** Identify exactly what broke without prematurely modifying production code.
2. **Propose Repair:** Suggest a backward-compatible SQL patch with zero revenue variance.
3. **Human Approval Gate:** Require explicit sign-off from the Data Owner before touching models.
4. **Dual-Fixture Verification:** Verify row counts and revenue across both legacy (`v2.8.0`) and drifted (`v3.0.0`) fixtures (100k rows in <50ms).
5. **Record Decision:** Write an immutable audit receipt to document human approval and restore the pipeline to green.

---

## 🏗️ Architecture & Components

```
                ┌─────────────────────────────────────────┐
                │   Telegram Group / Switch Room          │
                │        (SchemaCourt War Room)           │
                └────────────────────┬────────────────────┘
                                     │
              ┌──────────────────────┴────────────────────┐
              ▼                                           ▼
     @alex_backend / @S0NG0KU9                    @Claude Code
     (Producer & Data Owner)                   (Autonomous Agent)
                                                          │
                         ┌────────────────────────────────┴───────────────┐
                         ▼                                                ▼
               DuckDB Audit Engine                            Live Streamlit Monitor
           (python agents/drift_sentry.py)                      (dashboard/app.py)
                         │                                                │
      ┌──────────────────┴──────────────────┐                             │
      ▼                                     ▼                             ▼
Legacy Parquet (v2.8)              Drifted Parquet (v3.0)        Auto-refreshes (1Hz)
  100,000 rows                         100,000 rows              Red on drift, Green on fix
  $17,200,000 baseline                 $17,200,000 verified
```

- **Switch AI Room (`SchemaCourt War Room`):** Bridges Telegram and Switch Console so teams and agents collaborate where people work.
- **`@Claude Code`:** Follows strict `CLAUDE.md` stage-gated rules (investigate ➔ propose ➔ await approval ➔ apply).
- **`@DriftSentry` (`agents/drift_sentry.py`):** In-memory DuckDB validation engine. Audits 100,000 Parquet rows across product tiers in under **50ms**.
- **Streamlit Monitor (`dashboard/app.py`):** 1Hz live dashboard with per-tier dual-fixture metrics and recorded approval status.
- **Audit Receipt (`data/last_decision.json`):** Timestamped JSON receipt recording approver, commit SHA, and verification proof.

---

## ⚡ Quickstart & 2-Minute Reproduction

### 1. Prerequisites
- Python 3.10+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Launch the Live Executive Monitor
```bash
streamlit run dashboard/app.py
```
*(The dashboard opens at `http://localhost:8501`)*

### 3. Simulate Upstream Schema Drift (Incident)
```bash
python -m agents.drift_sentry --simulate-change
```
*Checkout-service drops `discount_cents` to NULL. Streamlit dashboard instantly turns **CRITICAL RED** ($17.2M revenue evaluates to NULL).*

### 4. Investigate & Propose in Switch / Telegram
In Telegram (`SchemaCourt War Room`), send:
```text
@claude checkout-service v3.0 broke discount_cents. Investigate and propose a fix for Maya to review.
```
*Claude reports the 100% null rate, shows the `COALESCE(discount_cents, promo_struct.discount_cents, 0)` SQL diff, and halts for Maya's approval.*

### 5. Human Sign-Off (Wispr Flow Voice Dictation)
Send:
```text
@claude approved by @maya_data. Apply the patch and verify both contracts.
```
*Claude patches `models/fct_revenue.sql`, runs DuckDB dual-audit across 200,000 rows ($0.00 delta), records the audit receipt, and Streamlit flips to **BRIGHT GREEN**!*

---

## 🏆 Built For
- **Track 1:** Best Business Workflow ($2,000)
- **Side Bounty:** Code with Wispr ($500 voice dictation bonus)
- **Event:** *Flip the Switch Hackathon* powered by Switch AI, WeMakeDevs & DevTools Academy.
