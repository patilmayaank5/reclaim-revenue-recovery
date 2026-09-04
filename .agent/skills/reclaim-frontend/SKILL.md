---
name: reclaim-frontend
description: Frontend architecture rules for the Reclaim Razorpay Buildathon project.
---

# Reclaim Frontend Rules

This skill is project-specific and takes priority over generic frontend
recommendations when they conflict with the frozen Reclaim architecture.

## Required Stack

Use:

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Recharts
- Lucide icons
- React Router
- TanStack Query where appropriate

## Do NOT introduce

Do not introduce:

- Material UI / MUI
- Chakra UI
- Ant Design
- Bootstrap
- another component framework

unless explicitly instructed.

## Architecture

The frontend is a presentation and interaction layer.

Business decisions must remain in the backend.

The frontend MUST NOT:

- calculate financial policy decisions
- authorize financial actions
- determine holdout assignment
- calculate authoritative recovery metrics
- directly call the Claude API
- contain Razorpay secret keys
- implement backend business rules

The backend is authoritative.

## AI

AI output comes from the backend.

The frontend should display:

- diagnosis
- evidence
- confidence
- candidate interventions
- expected value
- policy decision
- approval requirement

Do not display raw model output as the primary UI.

## Money

Never use floating-point arithmetic for authoritative monetary values.

Money received from the API should be represented using integer minor units
or a safe money representation.

## Case Timeline

Case timelines must be rendered from backend state/events.

Do not fabricate frontend-only state transitions.

## Demo Reliability

Demo mode must be deterministic.

The frontend should support the predefined Reclaim demo scenarios without
depending on unpredictable AI output.

## Design

The product should look like a professional fintech operations control room.

Avoid:

- generic SaaS dashboards
- excessive gradients
- unnecessary glassmorphism
- oversized hero sections
- decorative AI animations
- meaningless charts

Prioritize:

- information density
- hierarchy
- financial clarity
- status visibility
- fast scanning
- human approval clarity
- case investigation
- experiment results
- auditability

## Accessibility

Use semantic HTML, keyboard-accessible interactions,
appropriate contrast, and accessible labels.

## Source of Truth

The frozen Reclaim architecture and backend API contracts are authoritative.

Skills provide implementation guidance but must not change the product
architecture without explicit approval.
