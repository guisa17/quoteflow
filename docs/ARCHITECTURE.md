# Architecture

How QuoteFlow is built, what backs the claims in the [README](../README.md), and how it was made. The specs, ADRs and build log it links to are in Spanish.

## Walkthrough

<table>
<tr>
<td width="50%" valign="top">

**1. The order is pasted as it arrived.** The sample cases cover all five outcomes.

<img src="img/nueva-solicitud.png" alt="New request form with the customer, the order text and sample-case buttons">

</td>
<td width="50%" valign="top">

**2. Within policy, the draft comes out.** 20 × 45.00 = 900.00, minus 8% = 828.00, plus 18% IGV = **977.04**. Every figure can be checked with a calculator.

<img src="img/folio-borrador.png" alt="Quote with a ready draft: quote, draft for the customer and audit log">

</td>
</tr>
<tr>
<td width="50%" valign="top">

**3. An exception waits for a person.** The graph pauses with `interrupt()` and its state stays in Postgres: if the backend goes down, the case is still there when it comes back. A decision without a name isn't allowed, and the same decision sent twice isn't applied twice.

<img src="img/folio-aprobacion.png" alt="Quote pending approval for exceeding the threshold, with the decision panel">

</td>
<td width="50%" valign="top">

**4. A manipulation attempt doesn't go unnoticed.** The order carries a "system note" asking to set the price to USD 1. The price doesn't change, and the case goes to human review with the reason in view.

<img src="img/folio-manipulacion.png" alt="Quote flagged as possible manipulation, with the audit line highlighted">

</td>
</tr>
<tr>
<td width="50%" valign="top"><img src="img/bandeja-oscuro.png" alt="Inbox in dark mode"></td>
<td width="50%" valign="top"><img src="img/movil.png" alt="Pending quote on a phone" width="60%"></td>
</tr>
</table>

<sub>Generated from the real app with <code>pnpm capturas</code>.</sub>

## The boundary

No arrow goes back from the domain to the model: the LLM never sees inventory or policy, and any price, stock or customer tier it tries to return is dropped when its output is validated. If the provider doesn't respond, the request is read by a rules extractor and the quote says so. **The system degrades, but it doesn't become wrong** ([ADR-002](adr/ADR-002-frontera-determinista.md), [ADR-004](adr/ADR-004-extractor-gemini-con-respaldo.md)). Graphify confirms it on the real code: there are no import cycles and no dependencies from `llm/` to the rules ([graphify/](graphify/README.md)).

## The full graph

```mermaid
flowchart TD
    start(["<b>Request</b><br/>customer + free text"])

    ingest["<b>ingest</b><br/>normalize, open the thread"]
    extract["<b>extract</b><br/>validated output · manipulation"]

    resolve_customer["<b>resolve_customer</b><br/>BR-08 · customer tier"]
    validate_request["<b>validate_request</b><br/>BR-10/11 · completeness"]
    resolve_catalog["<b>resolve_catalog</b><br/>BR-02 · exact match"]
    check_inventory["<b>check_inventory</b><br/>BR-13 · on_hand − reserved"]

    price_quote["<b>price_quote</b><br/>RF-06 · Decimal"]
    evaluate_policy["<b>evaluate_policy</b><br/>BR-05 to BR-09 · BR-18"]

    human_approval["<b>human_approval</b><br/>RF-07 · durable interrupt()"]
    apply_decision["<b>apply_decision</b><br/>BR-15 · idempotent"]

    compose_draft["<b>compose_draft</b><br/>deterministic template"]

    clar(["NEEDS_CLARIFICATION"])
    blocked(["BLOCKED"])
    rejected(["REJECTED_BY_POLICY"])
    pending(["PENDING_APPROVAL"])
    draft(["DRAFT_READY"])

    start --> ingest --> extract
    extract -->|"retry"| extract
    extract --> resolve_customer --> validate_request --> resolve_catalog --> check_inventory
    check_inventory --> price_quote --> evaluate_policy
    evaluate_policy -->|"needs approval"| human_approval
    human_approval --> apply_decision
    apply_decision -->|"OBSERVE"| human_approval
    evaluate_policy -->|"within policy"| compose_draft
    apply_decision -->|"APPROVE"| compose_draft
    compose_draft --> draft

    extract -.->|"fails twice"| clar
    validate_request -.->|"missing info"| clar
    resolve_catalog -.->|"unknown SKU"| blocked
    check_inventory -.->|"out of stock"| blocked
    evaluate_policy -.->|"over the hard ceiling"| rejected
    apply_decision -.->|"REJECT"| rejected
    human_approval -.->|"while waiting"| pending

    classDef src fill:#f1f5f9,stroke:#64748b,color:#0f172a
    classDef llm fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#451a03
    classDef det fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
    classDef hum fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#2e1065
    classDef r_ok fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#052e16
    classDef r_wait fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#2e1065
    classDef r_ask fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#451a03
    classDef r_stop fill:#e2e8f0,stroke:#475569,stroke-width:2px,color:#0f172a
    classDef r_no fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#450a0a
    class start src
    class extract llm
    class ingest,resolve_customer,validate_request,resolve_catalog,check_inventory,price_quote,evaluate_policy,apply_decision,compose_draft det
    class human_approval hum
    class draft r_ok
    class pending r_wait
    class clar r_ask
    class blocked r_stop
    class rejected r_no
```

Yellow: the model. Blue: deterministic domain. Purple: human decision. Dashed arrows are early exits; they all go through `finalize`, which sets `outcome` and `reason_code`, and is left out of the drawing so the arrows don't cross. `PENDING_APPROVAL` isn't written by `finalize`: it's the state *observed* while the graph is paused. Every rule cited (`BR-xx`, `RF-xx`) is defined in [REQUIREMENTS.md](REQUIREMENTS.md) and referenced from the code and the tests.

## Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Orchestration | **LangGraph** (Pydantic-typed state, `interrupt()`) | The human pause has to survive a process restart |
| Persistence | **Postgres** + `AsyncPostgresSaver` | The checkpointer and the inbox live in one database ([ADR-003](adr/ADR-003-persistencia-checkpointer.md)) |
| API | **FastAPI**, psycopg 3 with pools | 4 endpoints; `409` on contradictory decisions, `503` if the database is down |
| Reading the text | **Any LLM** via `LLM_MODEL=provider:model`: Gemini over REST by default; Claude, OpenAI, Ollama and the rest of LangChain's providers | Schema-forced output and the same validation for all; fallback to a rules extractor ([ADR-006](adr/ADR-006-proveedor-llm-intercambiable.md)) |
| Frontend | **React 19**, Vite 8, Tailwind 4, TanStack Query, TypeScript 7 | Demo mode with the engine in the browser, and HTTP mode against the API |
| Observability | **LangSmith** (optional) | Node-by-node trace of each request, with model, tokens and cost |
| Quality | pytest, Vitest, **Playwright**, ruff, mypy, pre-commit, Dependabot, GitHub Actions | See below |

## What backs it

| What | Result |
|------|--------|
| Backend: unit, integration with real Postgres, API | **241** tests, no LLM calls |
| Frontend: demo engine, parity with the backend data, inbox URL | **47** tests |
| End-to-end in a browser (desktop and mobile) | **12** Playwright runs |
| **Reading with the real model**: 22 cases (scenarios, natural language, ambiguous, manipulation) | **31/31 items (100%)**, 22/22 cases. Business target: ≥ 90% |
| The same evals with the rules extractor (the fallback) | 22/31 items (71%): fine for the scenarios, not for natural language |
| CI with three required jobs; `main` only accepts green PRs | Backend · Frontend · E2E |
| Types and style | `mypy` over the whole backend, `ruff`, pre-commit hooks |
| Repository security | `gitleaks` over the full history: no secrets. `pip-audit` and `pnpm audit`: no known vulnerabilities |

The real-model evals run by hand because they spend quota ([backend/evals/](../backend/evals/README.md)). The first run found three bugs the tests hadn't: `bt 900` was read as `BT900` and the catalog didn't find it, "si aprueban esta cotización" ("if you approve this quote") was flagged as manipulation, and the rules extractor read "7,5 %" as 5%.

**The most valuable findings didn't come from the suite**, but from running the system for real. They're logged with real output in [EVIDENCE.md](proceso/EVIDENCE.md):

- `uvicorn` ignored the `asyncio` event loop policy on Windows and broke `psycopg` with the real server, even though the tests passed (E-11).
- Cloning the repo clean showed that the root `.env` was never read; the system *seemed* to work because the defaults matched (E-12).
- After a Postgres restart, the backend took **127 s** to recover. Now it's under 2 s (E-13).

### LangSmith traces

<table>
<tr>
<td width="50%" valign="top">

**The manipulation attempt, from the inside.** The model read the order correctly (`LN-120 × 40`), didn't obey the note and flagged it with `injection_suspected: true`.

<img src="img/langsmith-manipulacion.png" alt="LangSmith trace: gemini.extract call with the manipulated text and output with injection_suspected true">

</td>
<td width="50%" valign="top">

**The fallback during a real outage.** Gemini didn't answer within 20 s, the rules extractor took over and the request carried on. The later human decision landed in the same thread.

<img src="img/langsmith-respaldo.png" alt="LangSmith trace: gemini.extract failing with ProviderUnavailable and the full graph that continued">

</td>
</tr>
</table>

## Architecture decisions

| ADR | Decision |
|-----|----------|
| [001](adr/ADR-001-datos-ficticios-propios.md) | Own fictional data, calibrated so all five outcomes can be checked by hand |
| [002](adr/ADR-002-frontera-determinista.md) | The LLM interprets; the domain calculates, decides and drafts |
| [003](adr/ADR-003-persistencia-checkpointer.md) | Postgres as LangGraph's checkpointer and as the inbox's source |
| [004](adr/ADR-004-extractor-gemini-con-respaldo.md) | Gemini with schema-forced output and an explicit, never silent, fallback |
| [005](adr/ADR-005-manipulacion-a-revision-humana.md) | A manipulation attempt sends the case to human review |
| [006](adr/ADR-006-proveedor-llm-intercambiable.md) | The LLM provider is chosen with `LLM_MODEL=provider:model`, with the same boundary for all |

Each ADR records the rejected alternatives and, when the implementation changed something, an amendments section.

## How it was built

QuoteFlow is also an exercise in **AI-agent-assisted development with engineering discipline**. The method is documented in [proceso/](proceso/README.md):

- **Spec before code.** The business case, the requirements with IDs (`BR-xx`, `RF-xx`, `AC-xx`) and the API contract were written first. Code and tests cite those IDs.
- **Separate roles.** A main session owned the domain, architecture and verification. Delegated sessions implemented against fixed contracts, and their work was accepted only after independent verification ([AI_USE.md](proceso/AI_USE.md) records what was accepted, what was rejected and why).
- **Persistent context.** [CLAUDE.md](../CLAUDE.md) sets the repository rules. [STATE.md](proceso/STATE.md) and [EVIDENCE.md](proceso/EVIDENCE.md) let work resume without depending on any conversation.
- **Evidence, not claims.** Each phase closes with real commands and outputs. Anything unverified is declared as such.
- **Structural map with Graphify**, regenerated each phase and checked against the business impact analysis ([IMPACT.md](IMPACT.md)).
- **Team workflow, even solo:** branches, Conventional Commits, PRs with required CI, SemVer releases ([releases](https://github.com/guisa17/quoteflow/releases)) and Dependabot.

## Layout

```
backend/
  app/domain/     deterministic rules: pricing, policy, validation, manipulation
  app/graph/      LangGraph graph: state, nodes, routes, checkpointer
  app/llm/        extractors (Gemini, any provider via LangChain), fallback and rules
  app/api/        FastAPI: endpoints, schemas, inbox
  app/data/       sample data, shared with the frontend demo
  evals/          22 cases against the real model
  tests/          unit and integration
frontend/
  src/features/   inbox, new request, quote detail, 404
  src/mocks/      demo engine (same rules, same data)
  e2e/            Playwright: journeys and the screenshot generator
docs/
  adr/            architecture decisions
  proceso/        state, evidence, AI use, build log
  graphify/       structural map of the backend
```

## Documentation (in Spanish)

| Document | Contents |
|----------|----------|
| [BUSINESS_CASE.md](BUSINESS_CASE.md) | User, problem, value, metrics, risks and autonomy level (2 of 4) |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Business rules, requirements and acceptance criteria with IDs |
| [PROJECT.md](PROJECT.md) | Scope, stack and architecture |
| [ROADMAP.md](ROADMAP.md) | Completed phases and known pending work |
| [API_CONTRACT.md](API_CONTRACT.md) | API contract, fixed before writing code on either side |
| [IMPACT.md](IMPACT.md) | What propagates when a policy changes |
| [DESIGN.md](../DESIGN.md) | The console's design system |
| [proceso/](proceso/README.md) | State, evidence with real outputs, and AI use |
