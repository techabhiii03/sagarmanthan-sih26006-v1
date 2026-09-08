# SagarManthan — Intelligent Freight Forecasting & Vessel Chartering Platform

**Smart India Hackathon 2026 · Problem Statement SIH26006**  
**Organization:** Ministry of Steel / SAIL  
**Theme:** Transportation & Logistics

> From reactive daily spot chartering → proactive, predictive multi-voyage decision intelligence for bulk cargo (coal) into East Coast India.

---

## What this system does

A logistics manager enters:

- Origin (e.g. Newcastle, Australia)
- Destination (e.g. Paradip)
- Cargo type & quantity
- Laycan / bunker assumptions

and receives a **unified decision**:

| Output | Description |
|--------|-------------|
| **BOOK / WAIT / AVOID** | Market-entry recommendation with optimal window |
| **Vessel type** | Handysize / Supramax / Panamax / Capesize ranked by total cost under **port constraints** |
| **Port feasibility** | Explicit draft / LOA / beam rejection reasons |
| **Voyage economics** | Freight + bunker + port + waiting + demurrage + deadhead |
| **Contract mix** | Spot vs 3-voyage vs 6-voyage with risk reduction |
| **Idle strategy** | Wait / reposition / alternative employment |
| **Risk profile** | Multi-dimensional score with explanations |
| **Expected savings** | ₹ Cr vs pure-spot baseline |

All figures are **calculated** from models and engines. Simulated data is clearly labelled **DEMONSTRATION DATA**.

---

## Architecture

```
React + TypeScript + Vite  →  FastAPI  →  Forecast / Vessel / Port / Voyage / Contract / Idle / Risk engines
```

- **ML:** XGBoost + Naive + Moving Average, chronological validation, MAPE/RMSE, feature importance
- **Optimization:** Constraint filtering + total-cost ranking + contract mix scoring
- **Maps:** Leaflet (origin–destination route)
- **Charts:** Recharts

---

## Quick Start

### Scripts (recommended)

```bash
bash scripts/run_backend.sh    # Terminal 1 → http://localhost:8000
bash scripts/run_frontend.sh   # Terminal 2 → http://localhost:5173
```

### Manual

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

**Frontend**
```bash
cd frontend && npm install && npm run dev
```

Full judge script: **DEMO_GUIDE.md**

---

## Demo workflow (5–8 min)

1. Open **Decision Center**
2. Origin: **Newcastle** · Destination: **Paradip** · Cargo: **coking_coal** · 80,000 MT
3. Click **Evaluate Requirement**
4. Observe: Decision (WAIT/BOOK), forecast chart, vessel table with rejection reasons, contract mix, idle, risk, savings
5. Go to **Scenario Analysis** → change cargo to 150,000 MT or destination to Dhamra or bunker +20% → recompute
6. Check **Freight Forecast** for model comparison & feature importance
7. **Idle & Positioning**, **Port Intelligence** & **Maritime Map**

---

## Key modules

| Module | Path |
|--------|------|
| Forecast engine | `backend/app/ml/forecast_engine.py` |
| Port constraints | `backend/app/services/port_engine.py` |
| Voyage cost / bunker | `backend/app/services/voyage_engine.py` |
| Vessel optimizer | `backend/app/services/vessel_optimizer.py` |
| Market entry | `backend/app/services/market_entry.py` |
| Contract mix | `backend/app/services/contract_optimizer.py` |
| Idle optimizer | `backend/app/services/idle_optimizer.py` |
| Risk engine | `backend/app/services/risk_engine.py` |
| Decision orchestrator | `backend/app/services/decision_engine.py` |

---

## Data note

All freight time series, congestion indices and some cost parameters are **synthetic / demonstration** values calibrated to realistic maritime relationships. They are **not** live AIS or commercial freight feeds. Port draft/LOA/beam figures are approximate public-domain ranges for prototype use.

---

## Team & license

Built for SIH 2026 as a production-style prototype.  
MIT-style use for evaluation and educational purposes.
