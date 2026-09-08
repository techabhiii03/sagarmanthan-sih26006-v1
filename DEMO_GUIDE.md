# SagarManthan — Live Demo Guide (SIH 2026 · SIH26006)

**Target duration:** 5–8 minutes  
**Audience:** Judges evaluating decision-intelligence depth, not just UI.

---

## Before demo

1. Start backend: `bash scripts/run_backend.sh` (or `uvicorn app.main:app --reload --port 8000`)
2. Start frontend: `bash scripts/run_frontend.sh` (or `npm run dev`)
3. Open http://localhost:5173
4. Optional: open http://localhost:8000/docs in a second tab to show real APIs

---

## Script

### 1. Hook (30 sec)
> “Today SAIL still books many single spot voyages. SagarManthan moves them to short/medium multi-voyage cover with a full decision engine — forecast, port constraints, vessel ranking, contract mix, idle, and risk — in one click.”

Show **Dashboard** briefly → click **Decision Center**.

### 2. Input (30 sec)
Enter (or already filled):
- Origin: **Newcastle**
- Destination: **Paradip**
- Cargo: **coking_coal**
- Quantity: **80,000 MT**
- Laycan: **2026-11-01**

Click **Evaluate Requirement**.

### 3. Big decision card (45 sec)
Point to:
- **WAIT** (or BOOK) with confidence %
- Current vs 14-day forecast
- Recommended vessel (usually Panamax for this parcel)
- Risk level
- Expected saving in ₹ Cr

> “This is not a hardcoded badge. The decision comes from forecast delta versus uncertainty band plus risk tolerance.”

### 4. Why + vessel table (60 sec)
- Scroll to explanation bullets
- Vessel table: show Capesize **REJECTED** with draft numbers (required 18 m vs Paradip 16.5 m)
- Panamax feasible and lowest cost/MT among feasible set

> “We never say ‘Capesize unsuitable’. We show exactly which constraint failed.”

### 5. Forecast page (45 sec)
Navigate to **Freight Forecast**:
- Model comparison chart (Naive / MA / XGBoost MAPE)
- Selected model
- Feature importance
- Drivers text

> “Chronological validation — no random shuffle of time series.”

### 6. Contract + Idle (45 sec)
- **Contract Optimizer**: mix 6-voyage / 3-voyage / spot, savings vs pure spot
- **Idle & Positioning**: best strategy and idle days reduced

> “Old world: five separate spot fixtures. New world: multi-voyage cover with quantified risk reduction.”

### 7. What-if (60 sec) — critical for judges
Go to **Scenario Analysis**:
- Change cargo to **150,000 MT** → recompute (may need Capesize-capable port or more voyages)
- Or destination **Dhamra** (deeper draft) → Capesize may become feasible
- Or bunker **+20%** → costs and ranking shift

> “The recommendation is live. Change assumptions and the whole pipeline re-runs.”

### 8. Map + Ports (30 sec)
- **Maritime Map**: route line Newcastle → Paradip, click ports for draft/LOA
- **Port Intelligence**: East Coast card grid

### 9. Close (20 sec)
- **Data & Models** page: provenance statement
- “All monetary figures and decisions are calculated. Simulated data is labelled. Ready for live freight feeds and AIS later.”

---

## Backup answers for judges

| Question | Answer |
|----------|--------|
| Is data live? | No — demonstration synthetic series calibrated to realistic levels, clearly labelled. |
| Why XGBoost not LSTM? | Better on small maritime series; validated by MAPE; LSTM not required for credibility. |
| How is WAIT decided? | Forecast 14d delta vs uncertainty band derived from RMSE/MAPE. |
| Why reject Capesize at Paradip? | Draft 18 m required vs port max 16.5 m — explicit in engine. |
| Can we plug real rates? | Yes — replace `freight_generator` with DB/API feed; same engines. |

---

## One-liner for score sheet

**SagarManthan = Forecast + Port constraints + Vessel cost ranking + Contract mix + Idle + Risk → single BOOK/WAIT/AVOID decision with ₹ savings.**
