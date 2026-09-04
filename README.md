# Reclaim â€” Revenue Recovery Intelligence Engine

> Razorpay Buildathon 2026 Â· Track 03 â€” AI Revenue Recovery

## 1. Project

Reclaim â€” Revenue Recovery Intelligence Engine.

## 2. Problem

Failed payments create recoverable revenue leakage, but blindly retrying payments is not intelligent recovery. Modern revenue recovery requires understanding *why* a payment failed and orchestrating the optimal intervention (e.g., smart retries, routing, user messaging) without violating risk policies or wasting resources.

## 3. Core Principle

```
AI reasons and recommends.
Deterministic code authorizes.
Execution performs.
Verification confirms.
Experimentation measures.
Audit records everything.
```

## 4. Architecture

Reclaim is built on a modular monolith architecture.

### Backend
- **Python 3.14+**
- **FastAPI**
- **PostgreSQL**
- **SQLAlchemy async**
- **Pydantic v2**
- **Alembic** for migrations

### Frontend
- **React**
- **TypeScript**
- **Vite**
- **Tailwind CSS**
- **React Router**
- **TanStack Query** (React Query)
- **Recharts**
- **Lucide** for icons

### AI
- **AIProvider abstraction** for easy swapping of LLM engines
- **ClaudeProvider** (Anthropic Claude 3.5 Sonnet)
- **FakeAIProvider** for deterministic testing
- **Structured Pydantic-validated output** for all LLM calls
- **AI remains advisory**: AI only provides diagnosis and candidate interventions; it never authorizes or executes financial actions.

## 5. End-to-End Flow

```
Payment event
â†’ risk detection
â†’ enrichment
â†’ deterministic treatment/holdout assignment
â†’ AI diagnosis
â†’ closed intervention candidates
â†’ deterministic probability calibration
â†’ ERV calculation
â†’ deterministic policy
â†’ automatic execution OR human approval
â†’ provider execution
â†’ verification
â†’ experiment aggregation
â†’ audit trail
```

## 6. Important Safety & Governance Rules

- **Money uses integer minor units**: All financial amounts use integer minor units (e.g., paise, cents). No floating-point arithmetic is used for authoritative monetary values.
- **AI cannot authorize or execute payments**: The AI engine is completely isolated from execution and policy limits.
- **Policy is deterministic**: Approval thresholds and rules execute deterministically in code.
- **Holdout cases never receive AI/interventions/actions**: Cases assigned to the holdout group are rigorously isolated to measure baseline recovery.
- **STOPPED cases do not proceed**: Terminal states instantly halt processing.
- **Execution success is not considered recovery until verification**: An execution provider's success only triggers a verification phase.
- **Ambiguous execution is not automatically retried**: Ambiguous network/provider timeouts require external verification, preventing duplicate charges.
- **Action idempotency is DB-enforced**: Unique constraints prevent duplicate executions.
- **Audit events are append-only**: Comprehensive compliance tracking.
- **Human approval exists for high-value/manual-review actions**: Recoveries exceeding automated thresholds are routed to operators.

## 7. Demo Mode

Reclaim features a built-in Demo Mode that deterministically drives the real domain services for judging and demonstration purposes. It executes four specific scenarios:

### Scenario 1: Auto Recovery
- **â‚¹800** recoverable failure (`insufficient_funds`)
- â†’ AI diagnosis
- â†’ `ALLOW_AUTO` policy evaluation
- â†’ Simulator execution
- â†’ Verification
- â†’ **Recovered**

### Scenario 2: Human Approval
- **â‚¹48,000** technical failure
- â†’ Exceeds real **â‚¹20,000** auto-approval threshold
- â†’ `REQUIRE_APPROVAL` policy evaluation
- â†’ `PENDING_APPROVAL` action state
- â†’ Human approval
- â†’ Execution/Verification

### Scenario 3: Terminal Stop
- `revoked_mandate` failure (Terminal)
- â†’ `STOPPED`
- â†’ Zero AI / intervention / action / approval / execution.

### Scenario 4: Experimentation & Holdout
- **100-case** experiment
- â†’ 90 Treatment
- â†’ 10 Holdout
- â†’ 45 Treatment recovered
- â†’ 2 Holdout naturally recovered
- â†’ Treatment recovery rate = **50% (5000 bps)**
- â†’ Holdout recovery rate = **20% (2000 bps)**
- â†’ Lift = **30% (3000 bps)**
- â†’ **27** incremental recovered cases
- â†’ **2,700,000 minor units (â‚¹27,000)** incremental recovery.

## 8. Setup

### Prerequisites
- Python 3.14+
- Node.js v18+
- PostgreSQL 15+

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate    # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables (create a `.env` file in `backend/` or export them):
   ```bash
   DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/reclaim_test"
   ANTHROPIC_API_KEY="your-api-key"
   ```
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

## 9. Testing

The backend includes a comprehensive `pytest` suite testing all orchestrators, providers, policies, and demo mode mechanics.

```bash
cd backend
python -m pytest tests/backend/ -v
```

## 10. Project Structure

```
Reclaim project/
â”œâ”€â”€ .agent/skills/          # AI agent skills and architecture rules
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/                # Application package (API, Domain, Services, Models)
â”‚   â””â”€â”€ tests/              # Backend test suite
â”œâ”€â”€ docs/                   # Architecture and design documentation
â””â”€â”€ frontend/
    â””â”€â”€ src/                # React components, pages, hooks, and API clients
```

## 11. Buildathon Positioning

Reclaim is designed for the **Razorpay AI Buildathon Track 03 â€” AI Revenue Recovery**.
It uses simulator and demo execution where appropriate. Real Razorpay API integration is limited to the documented provider capability. This is a hackathon submission demonstrating an intelligent architectural pattern, not a guaranteed-recovery bank-grade production integration.

## 12. Demo Instructions

To run the Demo Mode for judges:
1. Start both the backend and frontend servers.
2. Navigate to the **Overview** dashboard in the web UI.
3. Locate the **Demo Mode Control Panel**.
4. Use the **Reset Demo** button to clear previous demo data without affecting real tenant records.
5. Click **Run Scenario 1**, **2**, **3**, or **4**.
6. Follow the provided links in the UI to observe the resulting Action, Case, or Experiment metrics live in the dashboard.
