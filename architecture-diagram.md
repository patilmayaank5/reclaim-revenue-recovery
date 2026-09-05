# Reclaim — Architecture / Decision Flow

This diagram is GitHub-renderable (paste directly into any `.md` file, or view this
file on GitHub). It distinguishes **AI reasoning**, **deterministic authorization**,
**human approval**, **execution**, **verification**, **experimentation**, and **audit**
by color, and shows the Treatment vs. Holdout split explicitly — Holdout never touches
AI, intervention, policy, or execution.

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

### Legend

| Color | Meaning |
|---|---|
| 🟣 Purple | AI reasoning (diagnosis + advisory probability only) |
| 🔵 Blue | Deterministic logic (detection, enrichment, assignment, candidate generation, ERV, policy) |
| 🟡 Amber | Human approval |
| 🟢 Green | Execution (provider abstraction) |
| 🟦 Teal | Verification (independent of execution) |
| 🌸 Pink | Experimentation / Holdout observation |
| ⬛ Gray | Audit trail (append-only, cross-cutting) |
| 🔴 Red | Blocked / no execution |

**Read the diagram left-to-right as a rule, not a suggestion:** the AI node only ever
feeds the deterministic Intervention Candidates step — there is no edge from AI
directly to Execution. Holdout cases physically cannot reach the AI, Policy, or
Execution nodes; the only path out of Holdout is "observe and measure."
