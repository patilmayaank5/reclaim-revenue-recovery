# Reclaim — Revenue Recovery Intelligence Engine

![Razorpay Buildathon 2026](https://img.shields.io/badge/Razorpay_Buildathon_2026-Track_03_—_AI_Revenue_Recovery-blue.svg)

> **Reclaim is a decision and measurement layer for revenue recovery — not just a retry engine.**

Reclaim ingests failed payment events, diagnoses *why* revenue is at risk, evaluates a
bounded set of recovery interventions, applies deterministic policy controls before any
money moves, routes high-value or sensitive cases to a human, independently verifies
whether recovery actually happened, and measures incremental impact against a holdout
group — with every material decision written to an append-only audit trail.

## Core Principle

```text
AI reasons.
Deterministic code authorizes.
Execution performs.
Verification confirms.
Experimentation measures.
Audit records.
```

Nothing in this pipeline lets a language model move money. The LLM produces a failure
diagnosis and an advisory recovery probability; every threshold check, authorization,
and financial action after that is decided by plain, testable, deterministic code.

## How Reclaim Works

Every payment failure enters the same pipeline, but **Treatment** and **Holdout** cases
experience it very differently from the moment they're assigned:

```mermaid
flowchart TD
    PE[Payment Event] --> RD[Risk Detection]
    RD --> EN[Enrichment]
    EN --> AS{Treatment / Holdout<br/>Assignment}

    AS -->|Holdout ~10%| HN[No AI · No Intervention<br/>No Action]
    HN --> HO[Observe Natural Recovery]

    AS -->|Treatment ~90%| AID[AI Diagnosis]
    AID --> IC[Intervention Candidates<br/>closed, bounded set]
    IC --> ERV[Expected Recovery Value<br/>ERV calculation]
    ERV --> POL{Deterministic Policy}

    POL -->|BLOCK| BLK[Blocked · No Execution]
    POL -->|REQUIRE_APPROVAL| HUM[Human Approval]
    POL -->|ALLOW_AUTO| EX[Execution Provider]
    HUM -->|Approved| EX
    HUM -->|Rejected| BLK

    EX --> VER[Verification<br/>independent of execution result]
    VER --> EXP[Experiment Measurement<br/>Treatment vs Holdout]
    HO --> EXP

    AS -.-> AUD[(Audit Trail)]
    POL -.-> AUD
    VER -.-> AUD
    EXP -.-> AUD
    BLK -.-> AUD

    classDef ai fill:#EDE9FE,stroke:#7C3AED,color:#3B0764,stroke-width:2px;
    classDef det fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A,stroke-width:2px;
    classDef human fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px;
    classDef exec fill:#D1FAE5,stroke:#059669,color:#064E3B,stroke-width:2px;
    classDef verify fill:#CCFBF1,stroke:#0D9488,color:#134E4A,stroke-width:2px;
    classDef experiment fill:#FCE7F3,stroke:#DB2777,color:#831843,stroke-width:2px;
    classDef audit fill:#E5E7EB,stroke:#4B5563,color:#111827,stroke-width:2px;
    classDef blocked fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D,stroke-width:2px;

    class RD,EN,AS,IC,ERV,POL det
    class AID ai
    class HUM human
    class EX exec
    class VER verify
    class EXP,HN,HO experiment
    class AUD audit
    class BLK blocked
```

**Treatment path:** Risk Detection → Enrichment → Assignment → **AI Diagnosis** →
Intervention Candidates → ERV → **Deterministic Policy** → Auto / Human Approval /
Block → Execution Provider → **Verification**

**Holdout path:** Risk Detection → Enrichment → Assignment → **stop.** No AI diagnosis,
no intervention candidates, no policy evaluation, no action, no execution. The case is
left alone and its payment status is observed for natural recovery.

Both cohorts feed **Experiment Measurement**, which compares Treatment's actual
recovery rate against Holdout's natural recovery rate to isolate the incremental effect
of Reclaim's interventions. Assignment, diagnosis, policy evaluation, execution,
verification, and aggregation are all written to an append-only **Audit Trail**.

### Stage-by-stage responsibility

| Stage | Responsibility | Controlled by |
|---|---|---|
| Detection | Classify a failed payment as revenue-at-risk and flag terminal failure codes (e.g. `revoked_mandate`, `card_expired`, `fraud_suspected`) for an immediate stop | Deterministic rules |
| Enrichment | Attach payment, merchant, and case context needed for diagnosis | Deterministic code |
| Assignment | Split each case into Treatment or Holdout *before* any AI involvement, via a stable hash | Deterministic hashing |
| Diagnosis | Infer the likely failure reason and an advisory recovery probability (Treatment cases only) | AI |
| Candidate generation | Map the diagnosis category to a closed set of up to 4 intervention types (smart retry, payment link, dunning email, manual review) | Deterministic code + AI diagnosis as an advisory input signal |
| ERV | Calibrate probability into basis points and compute `P(recovery) × Recoverable Amount − Intervention Cost − Risk Penalty` | Deterministic calculation |
| Policy | Decide `ALLOW_AUTO` / `REQUIRE_APPROVAL` / `BLOCK` against economic viability, fraud, and value-ceiling rules | Deterministic rules |
| Execution | Perform the authorized intervention through a provider abstraction | Provider abstraction (Simulator / Razorpay) |
| Verification | Confirm actual recovery from payment status/events — independent of execution's own success signal | Provider / payment state |
| Experimentation | Compare Treatment vs. Holdout recovery to compute lift and incremental recovery | Deterministic aggregation |
| Audit | Append-only, immutable record of every state transition and decision | Append-only audit log |

## Why This Isn't a Retry Engine

- **Not every failed payment is retried.** Terminal failure codes stop the case
  immediately — no diagnosis, no candidates, no action.
- **AI diagnoses; it never authorizes money movement.** Diagnosis output feeds a
  deterministic candidate map and calibration curve — the model has no path to an
  execution API.
- **Intervention choice is bounded.** Each failure category maps to a closed set of at
  most 4 deterministic intervention types, not open-ended model-directed action.
- **ERV decides economic worth.** `P(recovery) × Amount − Cost − Risk Penalty` must be
  positive or the candidate is blocked outright, regardless of what the model estimated.
- **A deterministic policy engine decides authorization** — `ALLOW_AUTO` /
  `REQUIRE_APPROVAL` / `BLOCK` — with fraud and value-ceiling rules that override
  everything else in the evaluation chain.
- **High-value actions require a human.** In the current policy configuration,
  interventions above ₹20,000 route to an approval queue instead of auto-executing.
- **Terminal failures stop instead of retrying** — `card_expired`,
  `customer_cancelled`, `fraud_suspected`, `account_closed`, `lost_card`, and
  `revoked_mandate` are all treated as unrecoverable by rule, not by model judgment.
- **Execution success ≠ recovery.** Only an independent verification step, reading
  actual payment status, is allowed to mark a payment as captured/recovered.
- **Treatment is compared against Holdout**, which receives no AI processing and no
  intervention at all, so natural recovery is measured rather than assumed away.
- **Incremental recovery (lift) is computed from that comparison**, not read off raw
  Treatment performance in isolation.
- **Every decision is auditable** — assignment, diagnosis, policy evaluation, execution
  attempts, and verification results are written to an append-only, ORM-enforced
  immutable audit trail.

## Measured Demo Result (Synthetic)

> **This is a deterministic, synthetic demo fixture that exercises the measurement
> pipeline end-to-end. It is not a production performance claim, not a guarantee of
> recovery, not a statistically significant result, and not derived from live
> transaction execution.**

100 seeded cases, ₹1,000 at risk each:

| | Treatment | Holdout |
|---|---|---|
| **Cases** | 90 | 10 |
| **Recovered** | 45 | 2 |
| **Recovery rate** | 50% | 20% |

- **Measured lift:** 30 percentage points (3,000 bps)
- **Incremental recovered cases:** 27
- **Incremental recovery:** ₹27,000

Holdout's 2 recoveries are natural/external — payment captured with **no** Reclaim
action, execution, or verification involved. The ₹27,000 figure is what the experiment
attributes to Reclaim's interventions beyond what would have recovered anyway.

## Demo Scenarios

Reclaim includes a deterministic Demo Mode to evaluate the architecture across four
scenarios:

| Scenario | Details | Flow |
|----------|---------|------|
| **Scenario 1: Auto Recovery** | ₹800 recoverable failure (`insufficient_funds`) | AI diagnosis → `ALLOW_AUTO` policy → auto execution → verification → **Recovered** |
| **Scenario 2: Human Approval** | ₹48,000 technical failure | Exceeds ₹20,000 auto threshold → `REQUIRE_APPROVAL` → `PENDING_APPROVAL` → human approval → execution → **Verification** |
| **Scenario 3: Terminal Stop** | `revoked_mandate` failure (Terminal) | `STOPPED` state → zero AI / intervention / action / approval / execution |
| **Scenario 4: Experimentation** | 100-case experiment | 90 Treatment vs 10 Holdout → Incremental recovery measured accurately |

## Safety & Governance

- **Money is represented in integer minor units.**
- **AI is advisory and cannot authorize financial actions.**
- **Policy decisions are deterministic.**
- **Holdout cases are excluded from the recovery intervention workflow.**
- **STOPPED cases do not continue.**
- **Execution success does not equal payment recovery.** Recovery requires
  verification.
- **Ambiguous execution is not automatically retried.**
- **Action idempotency is database-enforced** (`idempotency_key` has a real UNIQUE
  constraint).
- **Audit events are append-only and immutable** — ORM-level guards reject any update
  or delete attempt on an `AuditEvent` record.
- **High-value/manual-review actions can require human approval.**

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python, FastAPI, PostgreSQL, SQLAlchemy async, Pydantic v2, Alembic |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Recharts, Lucide |
| **AI** | `AIProvider` abstraction, `ClaudeProvider`, `FakeAIProvider`, structured Pydantic validation |
| **Execution** | `ExecutionProvider` abstraction, `SimulatorProvider`, `RazorpayProvider` |

## Setup

### Prerequisites
- Python 3.11+
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
*Note: The project includes a `FakeAIProvider` for deterministic testing if a real
Anthropic key is unavailable.*

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

This project is submitted for the **Razorpay AI Buildathon 2026 · Track 03 — AI
Revenue Recovery**.

- `SimulatorProvider` drives deterministic demo execution and verification with zero
  randomness.
- `RazorpayProvider` validates that Razorpay credentials are configured and, for the
  `payment_link` intervention type, exercises the structured request/response
  boundary a real Payment Links integration would use. In this snapshot it returns a
  synthetic transaction/event ID rather than making a live HTTP call to Razorpay's
  API — it demonstrates the integration boundary and credential gating, not a
  production Razorpay connection. All other intervention types (smart retry, dunning
  email) are explicitly rejected by this provider rather than simulated as if Razorpay
  supported them natively, since Razorpay does not expose a generic automated-retry or
  email-dunning REST API.
- This is a buildathon prototype demonstrating the architecture and decision
  discipline described above, not a bank-grade production integration.
