# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Operator (in-product):** an inside-sales executive at a B2B distributor of industrial personal protective equipment (EPP). They receive quote requests as free text (email, forms, messaging) and must turn each one into a correct quote or a clear next step, many times a day.
- **Approver:** a commercial lead who resolves the cases the system pauses for human decision (amount over threshold, discount exception, unknown customer).
- **Portfolio audience (confirmed, equal weight):** technical recruiters who open the live demo for a minute or two, and prospective clients (commercial managers at distributors). Both must grasp within seconds how free text becomes an auditable decision.

## Product Purpose

QuoteFlow turns a free-text quote request into one of five auditable outcomes: `NEEDS_CLARIFICATION`, `DRAFT_READY`, `BLOCKED`, `PENDING_APPROVAL`, `REJECTED_BY_POLICY`. It prepares drafts; it never sends anything to the customer. Success is a faster quote without compromising margin, stock or human control.

## Positioning

The model only interprets text; every price, stock check, discount limit and approval comes from deterministic domain code, and every step is recorded. A request that needs a human genuinely pauses and survives a backend restart. The interface's job is to make that reasoning visible, not to hide it behind a verdict.

## Operating Context

- Three destinations: inbox (requests with outcome and reason), new request (customer + free text), request detail (original text, extraction, quote lines, reasons, decision panel, draft, audit trail).
- Decisions: approve, reject, observe (keeps the case paused). A conflicting decision returns 409 and must be shown, not swallowed.
- Two data modes: `mock` (rules engine in the browser, seeded with 8 scenarios) for the public demo, `http` for the real API.
- Money is decimal strings, currency USD, IGV 18 %. Figures and SKUs read as tabular data.

## Capabilities and Constraints

- Stack: React 19 + Vite + Tailwind 4 + shadcn/ui primitives, React Query, react-router. Spanish UI only.
- No authentication yet: the actor is typed by the user. Do not imply login, roles or identity verification.
- The extractor is a deterministic test double, not an LLM. Do not claim "AI" in the UI.
- Must work in both light and dark themes (confirmed requirement).

## Brand Commitments

- Name: QuoteFlow. Demo company: Ferrocima Industrial (fictional). Customer IDs `FER-1001…1003`.

## Evidence on Hand

- 8 seeded scenarios in `backend/app/data/sample_requests.json`, mirrored in `frontend/src/mocks/data.ts`, with hand-verifiable figures (S1: 900.00 → 72.00 → 828.00 → IGV 149.04 → 977.04).
- No real customers, testimonials, metrics or pricing exist. Business-case figures are assumptions and must not appear as results.

## Product Principles

1. Show the reasoning: what was extracted, which rule fired, who decided, in order.
2. Density over decoration: an operator scans many requests; speed of reading wins.
3. The human decision is the moment that matters; it must never be ambiguous or lost.
4. Never fabricate: every number on screen comes from the domain.

## Accessibility & Inclusion

WCAG 2.1 AA contrast in both themes; keyboard operable decisions; status never conveyed by color alone.
