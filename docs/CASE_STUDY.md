# SalesFlow AI — Engineering Case Study

## Problem

Many small sales teams acquire leads through forms but lose the context between capture and conversation. Qualification varies by salesperson, follow-up timing depends on memory, booking data lives elsewhere, and leaders cannot explain why an opportunity moved—or stalled.

## Solution

SalesFlow AI creates one observable revenue loop. A contextual public funnel creates a durable lead. AI converts the answers into a strict qualification object. n8n selects an appropriate response path, Resend delivers a human-sounding follow-up, Cal.com handles scheduling, and the CRM presents the resulting score, history and pipeline state in one place.

## Architecture

The product is a monorepo with a separately deployable Next.js frontend and FastAPI backend. PostgreSQL owns normalized operational data. n8n is intentionally an orchestrator rather than a second backend: workflows call versioned API endpoints and never mutate product tables directly. This boundary makes retry and audit behavior explicit.

## AI qualification approach

The form captures role, company profile, stated need, budget and timeline because these provide meaningful buying evidence. The workflow calls the OpenAI Responses API with strict Structured Outputs. Its JSON Schema bounds the score, enumerates classification/intent/fit/urgency and requires every sales-facing field. FastAPI validates that object again with Pydantic and enforces the temperature thresholds in application code. A malformed or contradictory answer cannot be persisted.

AI failure is non-destructive: lead persistence precedes the background webhook. The timeline records a failed automation, and the opportunity remains available for manual triage.

## Automation architecture

Four production workflows divide responsibilities:

1. **Lead Qualification** validates the signed webhook, calls OpenAI, persists the structured result, then branches on temperature.
2. **Hot Lead Follow-Up** sends a priority, personalized email with a direct demo booking CTA and records the provider event.
3. **Warm Lead Nurture** sends a lower-pressure message and begins a longer follow-up window.
4. **Appointment Event** normalizes a Cal.com event, associates the attendee with the newest matching lead, advances the pipeline and appends a timeline event.

Unique idempotency keys protect appointment and execution callbacks from provider retries. HTTP timeouts, bounded retries and visible failure events treat every external service as unreliable by default.

## CRM architecture

The schema separates users, leads, qualifications, activities, notes, emails, appointments and automation runs. Lead profiles aggregate those relations into a decision-ready record. Pipeline transitions write an activity in the same database transaction. Analytics queries calculate from stored records instead of maintaining fragile counters.

The frontend polls selected operational queries at short intervals. This is simpler to operate than WebSockets and provides the immediacy required for a live demonstration without introducing another stateful channel.

## Key engineering decisions

- **API as source of truth:** workflows are replaceable; product state remains consistent.
- **Persist first, automate second:** third-party outages never discard a lead.
- **Two-layer AI validation:** schema-constrained generation plus domain validation.
- **Explicit migrations:** production never depends on ORM table creation at startup.
- **Restrained design system:** editorial typography, warm neutrals, deliberate density and narrow accent usage create a credible B2B product instead of a generic template.
- **Marked sample data:** demonstration value without misleading portfolio viewers.

## Security considerations

Argon2 protects administrator passwords. JWTs have bounded lifetimes. Public submission is rate-limited and every string has a server-side length limit. CORS is explicit. OpenAI and Resend credentials never enter the client bundle. Internal callbacks use isolated shared secrets and constant-time comparison. Production secrets are environment-managed and excluded from Git.

## Challenges

The most important integration challenge is keeping a multi-service workflow explainable when callbacks can be delayed, duplicated or fail. The activity model and idempotency constraints turn those conditions into visible domain events. Cal.com account tiers can also vary in webhook access; the architecture supports direct webhook delivery, n8n integration or controlled polling without changing the CRM contract.

## Outcome

The result demonstrates the complete lifecycle expected from a production SaaS portfolio project: acquisition UX, protected CRM, normalized data, AI reasoning with deterministic contracts, workflow automation, transactional email, appointment synchronization, analytics, containerization, migrations, tests and multi-service deployment.

## Technologies

Next.js, React, TypeScript, Tailwind CSS, TanStack Query, Recharts, FastAPI, Python, SQLAlchemy, Pydantic, Alembic, PostgreSQL, n8n, OpenAI, Resend, Cal.com, Docker, Docker Compose, Dokploy and GitHub.

