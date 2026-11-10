"""Eleccion del extractor real a partir de la configuracion (ADR-006).

Un solo punto decide que proveedor lee el texto, para que el grafo y las
evals usen exactamente el mismo extractor. `LLM_MODEL` sigue la convencion
`proveedor:modelo` de LangChain, LiteLLM y Pydantic AI:

- vacio o `gemini:<modelo>`: `GeminiExtractor`, por REST y sin dependencias.
  Es el camino medido en las evals (ADR-004).
- cualquier otro proveedor: `LangChainExtractor` con `init_chat_model`.
"""

from dataclasses import dataclass

from app.config import Settings
from app.llm.base import Extractor
from app.llm.gemini_extractor import GeminiExtractor
from app.llm.langchain_extractor import LangChainExtractor, LLMConfigError

NATIVE_GEMINI = "gemini"


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"


def parse_model_spec(settings: Settings, override: str | None = None) -> ModelSpec:
    value = (override if override is not None else settings.llm_model).strip()
    if not value:
        return ModelSpec(NATIVE_GEMINI, settings.gemini_model)
    provider, sep, model = value.partition(":")
    if not sep or not provider or not model:
        raise LLMConfigError(
            f"LLM_MODEL={value!r} no tiene la forma proveedor:modelo "
            "(p. ej. gemini:gemini-3.5-flash-lite o anthropic:claude-haiku-5-5)."
        )
    return ModelSpec(provider.strip().lower(), model.strip())


def build_llm_extractor(settings: Settings, model_override: str | None = None) -> Extractor:
    """El extractor real, sin respaldo: `build.py` lo envuelve en
    `FallbackExtractor`; las evals lo usan tal cual, para medir al modelo."""
    spec = parse_model_spec(settings, model_override)
    if spec.provider == NATIVE_GEMINI:
        return GeminiExtractor(
            api_key=settings.llm_api_key or settings.gemini_api_key,
            model=spec.model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return LangChainExtractor(
        spec.provider,
        spec.model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        structured_output=settings.llm_structured_output,
    )
