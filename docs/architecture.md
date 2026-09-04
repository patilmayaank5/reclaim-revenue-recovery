# Reclaim â€” Frozen Architecture Reference

This document summarises the frozen Reclaim architecture.
It is the source of truth for all implementation decisions.

## Core Principle

```
AI reasons and recommends.
Deterministic code authorizes.
Execution performs.
Verification confirms.
Experimentation measures.
Audit records everything.
```

## Recovery Pipeline

1. **Detection** â€” Identify revenue-at-risk cases.
2. **Enrichment** â€” Gather relevant context for each case.
3. **Diagnosis** â€” AI diagnoses the likely failure reason.
4. **Intervention Generation** â€” AI produces a closed set of candidate interventions.
5. **Expected Value Calculation** â€” Deterministic ERV computation:
   ```
   ERV = P(recovery) Ã— Recoverable Amount âˆ’ Intervention Cost âˆ’ Risk Penalty
   ```
6. **Policy** â€” Deterministic policy rules decide authorization.
7. **Routing** â€” Actions route to automatic execution or human approval.
8. **Execution** â€” Provider abstraction executes the action.
9. **Verification** â€” Confirm actual recovery through payment status/events.
10. **Audit** â€” Append-only, immutable audit trail.
11. **Experimentation** â€” Treatment/holdout measurement of incremental lift.
12. **Analytics** â€” Segment-level intervention analytics.

## Hard Rules

### Money
- Integer minor units only.
- No floating-point for authoritative monetary values.

### Policy Engine
- Fully deterministic.
- LLM never authorizes, sets limits, assigns holdouts, or executes.

### Holdout
- Assignment happens deterministically BEFORE AI processing.
- Holdout cases receive no AI processing or intervention.

### Execution
- Provider abstraction: `ExecutionProvider â†’ RazorpayProvider | SimulatorProvider | DemoProvider`
- Do not invent Razorpay APIs.

### Verification
- HTTP 200 is not sufficient to declare recovery.
- Must use payment status/event verification.

### Idempotency
- Enforced by database uniqueness constraints.

### Audit
- Append-only, immutable records.

### AI
- Single AI orchestrator.
- Structured, validated output.
- AI never directly authorizes financial actions.

### Frontend
- Presentation and interaction layer only.
- No business rules, no financial policy, no holdout logic.
- No direct Claude calls.

## Tech Stack

| Layer | Stack |
|:------|:------|
| Backend | Python, FastAPI, PostgreSQL, SQLAlchemy async, Pydantic v2 |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Recharts, Lucide, React Router, TanStack Query |
| AI | Claude via Anthropic SDK, behind single orchestrator |
| Architecture | Modular monolith |

## Core UI Screens

- Overview / Control Room
- Live Recovery
- Cases / Case Investigation
- Approval Queue
- Experiments
- Analytics
- Policies
- Audit
