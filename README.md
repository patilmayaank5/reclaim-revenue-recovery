# Reclaim — Revenue Recovery Intelligence Engine

![Razorpay Buildathon 2026](https://img.shields.io/badge/Razorpay_Buildathon_2026-Track_03_—_AI_Revenue_Recovery-blue.svg)

Reclaim is an AI-powered revenue recovery intelligence engine for failed payments. It diagnoses why revenue is at risk, evaluates bounded recovery interventions, applies deterministic policy controls, routes sensitive cases to humans, verifies actual outcomes, and measures incremental recovery against a holdout group.

## Why Reclaim?

**Traditional Retry Systems:**
- Blindly retry harder without diagnosis
- Limited governance or bounds on interventions
- Success is often conflated with true recovery
- Little to no experimental measurement

**Reclaim:**
- **Diagnoses** the true failure reason
- **Generates** a closed, bounded set of intervention candidates
- **Calculates** deterministic Expected Recoverable Value (ERV)
- **Enforces** deterministic policy limits
- **Routes** high-risk or sensitive cases for human approval
- **Verifies** payment recovery independently of execution success
- **Compares** treatment recovery against a rigorous holdout group
- **Preserves** an append-only, comprehensive audit trail

## Core Principle

```text
AI reasons and recommends.
Deterministic code authorizes.
Execution performs.
Verification confirms.
Experimentation measures.
Audit records everything.
```

## What Is AI vs Deterministic?

**AI (The Brain)** is responsible for:
- Diagnosing the likely failure reason from context.
- Producing an advisory recovery probability.
- Informing a closed set of intervention candidates (e.g., smart retry, dunning).

*The LLM can recommend; it cannot decide whether money-moving behavior is allowed.*

**Deterministic Systems (The Engine)** are responsible for:
- Treatment/holdout assignment.
- Probability calibration and ERV calculation.
- Policy authorization (ALLOW_AUTO, REQUIRE_APPROVAL, BLOCK).
- Action creation and provider execution.
- Payment outcome verification.
- Experiment aggregation and measurement.
- Append-only auditing.

## Architecture

```text
Payment Event
     ↓
Risk Detection
     ↓
Enrichment
     ↓
Treatment / Holdout Assignment
     ↓
AI Diagnosis
     ↓
Closed Intervention Candidates
     ↓
Probability Calibration + ERV
     ↓
Deterministic Policy Engine
     ├── BLOCK
     ├── REQUIRE_APPROVAL → Human
     └── ALLOW_AUTO
              ↓
       Execution Provider
              ↓
          Verification
              ↓
     Experiment Aggregation
              ↓
          Audit Trail
```

## Measured Demo Result

*This is a deterministic synthetic demo fixture for demonstrating the measurement workflow, not a production performance claim.*

| Metric | Treatment | Holdout |
|--------|-----------|---------|
| **Cases** | 90 | 10 |
| **Recovered** | 45 | 2 |
| **Recovery Rate** | 50% | 20% |

- **Measured lift:** 30 percentage points (3000 bps)
- **Incremental recovered cases:** 27
- **Incremental recovery:** 2,700,000 minor units (₹27,000)

*Note: Treatment recovery happens through the full Reclaim AI workflow. Holdout recovery represents natural/external recovery captured directly via payment status. Holdout cases do NOT receive AI diagnosis, interventions, actions, execution, or verification.*

## Demo Scenarios

Reclaim includes a deterministic Demo Mode to evaluate the architecture across four scenarios:

| Scenario | Details | Flow |
|----------|---------|------|
| **Scenario 1: Auto Recovery** | ₹800 recoverable failure (`insufficient_funds`) | AI diagnosis → `ALLOW_AUTO` policy → auto execution → verification → **Recovered** |
| **Scenario 2: Human Approval** | ₹48,000 technical failure | Exceeds ₹20,000 auto threshold → `REQUIRE_APPROVAL` → `PENDING_APPROVAL` → human approval → execution → **Verification** |
| **Scenario 3: Terminal Stop** | `revoked_mandate` failure (Terminal) | `STOPPED` state → zero AI / intervention / action / approval / execution |
| **Scenario 4: Experimentation**| 100-case experiment | 90 Treatment vs 10 Holdout → Incremental recovery measured accurately |

## Safety & Governance

- **Money is represented in integer minor units.**
- **AI is advisory and cannot authorize financial actions.**
- **Policy decisions are deterministic.**
- **Holdout cases are excluded from the recovery intervention workflow.**
- **STOPPED cases do not continue.**
- **Execution success does not equal payment recovery.** Recovery requires verification.
- **Ambiguous execution is not automatically retried.**
- **Action idempotency is database-enforced.**
- **Audit events are append-only.**
- **High-value/manual-review actions can require human approval.**

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python, FastAPI, PostgreSQL, SQLAlchemy async, Pydantic v2, Alembic |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Recharts, Lucide |
| **AI** | AIProvider abstraction, ClaudeProvider, FakeAIProvider, structured Pydantic validation |
| **Execution** | ExecutionProvider abstraction, SimulatorProvider, RazorpayProvider |

## Setup

### Prerequisites
- Python 3.14+
- Node.js v18+
- PostgreSQL 15+

### Running the Project

Navigate to the repository root:
```bash
cd "Reclaim project"
```

**1. Backend Setup**
```bash
cd backend
python -m venv .venv

# Activate the virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

**2. Environment Variables**
Create a `.env` file in the `backend/` directory with a safe placeholder:
```env
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/reclaim_test"
ANTHROPIC_API_KEY="your-api-key"
```
*Note: The project includes a `FakeAIProvider` for deterministic testing if a real Anthropic key is unavailable.*

**3. Database Migrations**
```bash
alembic upgrade head
```

**4. Start Backend Server**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

**5. Start Frontend Server**
Open a new terminal to the repository root:
```bash
cd frontend
npm install
npm run dev
```

## Verification

- **Backend:** 149 tests passing
- **Frontend:** lint passing (`npm run lint`)
- **Frontend:** production build passing (`npm run build`)
- **PostgreSQL:** Migration chain verified
- **Integration:** Demo scenarios verified end-to-end

### Running Tests

The test suite is rooted at the repository level.

```powershell
cd "Reclaim project"
$env:PYTHONPATH="."
pytest -v
```
*(On macOS/Linux, use `PYTHONPATH="." python -m pytest -v`)*

## Demo Instructions

To run the Demo Mode for judges:
1. Start PostgreSQL.
2. Start the backend.
3. Start the frontend.
4. Open the Overview dashboard.
5. Click **Reset Demo**.
6. Run **Scenario 1**.
7. Run **Scenario 2** and approve the pending action.
8. Run **Scenario 3**.
9. Run **Scenario 4**.
10. Open **Experiments / Analytics** to show measured lift.
11. Open **Audit** to show the decision trail.

## Repository Structure

```text
Reclaim project/
├── .agent/skills/    → Antigravity agent skills and project-specific guidance
├── backend/
│   ├── app/api/      → HTTP API
│   ├── app/domain/   → deterministic domain rules and provider abstractions
│   ├── app/models/   → persistence model
│   └── app/services/ → orchestration and workflows
├── docs/             → architecture documentation
├── frontend/src/     → dashboard and operational UI
├── tests/backend/    → backend regression suite
└── README.md
```

## Buildathon Positioning / Limitations

This project is submitted for the **Razorpay AI Buildathon 2026 · Track 03 — AI Revenue Recovery**.
`SimulatorProvider` is used for deterministic demo execution. Razorpay integration is limited to the documented provider capability implemented in the repository. The project does not pretend to have a universal Razorpay retry API. Dunning email and smart retry are simulated where the provider abstraction does not expose a corresponding real API. This is a buildathon prototype demonstrating the architecture, not a bank-grade production integration.
