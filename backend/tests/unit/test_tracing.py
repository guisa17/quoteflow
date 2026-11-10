"""Trazas de LangSmith sin red.

`tracing_context(enabled="local")` construye las trazas igual que en uso real
pero nunca las envia (la SDK solo hace `patch()` hacia el servidor cuando el
modo es exactamente `True`). `on_end` entrega la traza terminada para
inspeccionarla."""

import json
import os
from typing import Any

import httpx
import pytest
from langsmith.run_helpers import tracing_context
from langsmith.run_trees import RunTree

from app.config import Settings, configure_tracing
from app.llm.fake_extractor import FakeExtractor
from app.llm.fallback import FallbackExtractor
from app.llm.gemini_extractor import GeminiExtractor

# En modo "local" la SDK crea un cliente sin key aunque nunca lo use para
# enviar; la advertencia es esperable aqui.
pytestmark = pytest.mark.filterwarnings("ignore::langsmith.utils.LangSmithMissingAPIKeyWarning")


def _gemini(status: int, body: dict[str, Any]) -> GeminiExtractor:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(status, json=body))
    )
    return GeminiExtractor(api_key="secreto-de-prueba", model="gemini-test", client=client)


OK_REPLY = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": json.dumps(
                            {"items": [{"product_reference": "HX-200", "quantity": 20}]}
                        )
                    }
                ]
            }
        }
    ],
    "modelVersion": "gemini-test-flash",
    "usageMetadata": {"promptTokenCount": 410, "candidatesTokenCount": 38, "totalTokenCount": 448},
}


def _usage(run: RunTree) -> dict[str, Any]:
    return (run.outputs or {}).get("usage_metadata") or run.metadata.get("usage_metadata") or {}


async def test_llm_trace_records_provider_model_and_tokens() -> None:
    captured: list[RunTree] = []
    with tracing_context(enabled="local"):
        await _gemini(200, OK_REPLY).extract(
            "20 cascos HX-200", langsmith_extra={"on_end": captured.append}
        )

    run = captured[0]
    assert run.run_type == "llm"
    assert run.name == "gemini.extract"
    assert run.metadata["ls_provider"] == "google"
    assert run.metadata["ls_model_name"] == "gemini-test-flash"
    assert _usage(run) == {"input_tokens": 410, "output_tokens": 38, "total_tokens": 448}


async def test_llm_trace_never_records_the_api_key() -> None:
    captured: list[RunTree] = []
    with tracing_context(enabled="local"):
        await _gemini(200, OK_REPLY).extract(
            "20 cascos HX-200", langsmith_extra={"on_end": captured.append}
        )

    assert captured[0].inputs == {"raw_text": "20 cascos HX-200"}
    assert "secreto-de-prueba" not in json.dumps(captured[0].inputs, default=str)


async def test_fallback_trace_is_tagged_with_reason() -> None:
    captured: list[RunTree] = []
    extractor = FallbackExtractor(primary=_gemini(429, {}), fallback=FakeExtractor())
    with tracing_context(enabled="local"):
        await extractor.extract("20 cascos HX-200", langsmith_extra={"on_end": captured.append})

    run = captured[0]
    assert run.name == "extractor"
    assert "respaldo" in (run.tags or [])
    assert "429" in run.metadata["fallback_reason"]


def test_configure_tracing_requires_flag_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # setenv antes de delenv: asi monkeypatch registra el estado original y lo
    # restaura al terminar, aunque configure_tracing escriba en os.environ.
    for var in (
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_ENDPOINT",
    ):
        monkeypatch.setenv(var, "")
        monkeypatch.delenv(var)

    assert not configure_tracing(
        Settings(langsmith_tracing=True, langsmith_api_key="", langsmith_endpoint="")
    )
    assert os.environ["LANGSMITH_TRACING"] == "false"

    assert not configure_tracing(
        Settings(langsmith_tracing=False, langsmith_api_key="lsv2-x", langsmith_endpoint="")
    )
    assert os.environ["LANGSMITH_TRACING"] == "false"

    assert configure_tracing(
        Settings(
            langsmith_tracing=True,
            langsmith_api_key="lsv2-x",
            langsmith_project="demo",
            langsmith_endpoint="",
        )
    )
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "lsv2-x"
    assert os.environ["LANGSMITH_PROJECT"] == "demo"
    assert "LANGSMITH_ENDPOINT" not in os.environ
