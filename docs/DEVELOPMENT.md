# Development

Running the full system, choosing an LLM, testing, and a demo script. For the browser-only demo, the [README](../README.md#try-it) is enough.

## Full system

**Requirements:** Python 3.12+ with [`uv`](https://docs.astral.sh/uv/), Node 22+ with `pnpm`, and Docker for Postgres.

```bash
# 1. Database
docker compose up -d                 # wait until it's healthy

# 2. Configuration
cp .env.example .env                 # the defaults work without an LLM

# 3. Backend: http://localhost:8000 (API docs at /docs)
cd backend
uv sync
uv run uvicorn app.main:app --loop app.main:loop_factory --reload

# 4. Frontend against the API
cd ../frontend
pnpm install
VITE_API_MODE=http pnpm dev          # http://localhost:5173
```

> **Why `--loop app.main:loop_factory`:** on Windows, `uvicorn` defaults to a `ProactorEventLoop`, which async `psycopg` doesn't support. The custom factory forces `SelectorEventLoop`, the only loop on Linux and macOS, so nothing changes there ([app/main.py](../backend/app/main.py)).

## With a real LLM

Set the mode and the model in `.env` (an optional `backend/.env` takes precedence over the root one). The quickest is Gemini, with a free key from [Google AI Studio](https://aistudio.google.com):

```bash
LLM_MODE=real
GEMINI_API_KEY=...                       # with LLM_MODEL empty, Gemini is used
```

For another provider, install its package and set two variables:

| Provider | Install (in `backend/`) | `.env` |
|----------|-------------------------|--------|
| Anthropic | `uv sync --extra anthropic` | `LLM_MODEL=anthropic:claude-haiku-5-5` and `LLM_API_KEY` |
| OpenAI | `uv sync --extra openai` | `LLM_MODEL=openai:gpt-5-mini` and `LLM_API_KEY` |
| Ollama (local, no key) | `uv sync --extra ollama` | `LLM_MODEL=ollama:llama3.2` |
| OpenAI-compatible (OpenRouter, vLLM, LM Studio...) | `uv sync --extra openai` | `LLM_MODEL=openai:<model>`, `LLM_BASE_URL` and `LLM_API_KEY` |
| Other LangChain providers (Mistral, Groq, Bedrock...) | `uv add langchain-<provider>` | `LLM_MODEL=<provider>:<model>` and `LLM_API_KEY` |

The prompt, schema and validation are the same for all. A misconfigured `LLM_MODEL` (unknown provider, missing package, no `provider:` prefix) stops the backend at startup with a message saying what to fix. Before trusting a new model, measure it with the evals: `uv run python -m evals.run --model provider:model`.

**With LangSmith traces (optional).** Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`. Each request becomes a tree of steps, with the model, tokens and latency of the LLM call. A request's registration and its decision share a thread. Tests never send traces.

## Tests

```bash
cd backend
uv run pytest                 # 241 tests (integration ones need Postgres)
uv run pytest tests/unit      # rules only, no Postgres
uv run ruff check . && uv run mypy app
uv run python -m evals.run    # evals against the LLM_MODEL model (needs its key)

cd ../frontend
pnpm test                     # 35 demo-engine tests
pnpm test:e2e                 # 10 Playwright journeys
pnpm typecheck && pnpm build
pnpm capturas                 # regenerate the screenshots in docs/img/
```

Pre-commit hooks (ruff, formatting, blocking `.env` files and private keys) are installed once per clone with `cd backend && uv run pre-commit install`.

## Demo script (about 5 minutes)

1. **Inbox:** requests with their outcome and reason. The "Por decidir" tab shows only what is waiting for a person.
2. **"Pedido estándar":** draft ready, with the figures from the [walkthrough](ARCHITECTURE.md#walkthrough). The "Recorrido" strip shows which steps ran.
3. **"Falta la cantidad":** the system asks for clarification instead of inventing a number.
4. **"Supera USD 10 000":** it stays pending. With the full system, **stop the backend**, start it again and reload: the case is still there. Approve it and the draft is generated.
5. **"Intento de manipulación":** the text asks for a 40% discount "approved by management". It ends rejected by policy, with no human decision recorded. The same manipulation in an order within policy goes to human review (BR-18).
6. **Live policy change:** edit the `GOLD` maximum in [`policies.json`](../backend/app/data/policies.json), restart and repeat step 2. The result changes without touching code ([IMPACT.md §2](IMPACT.md)).
