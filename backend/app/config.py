import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Rutas absolutas, no relativas al directorio de trabajo. `env_file=".env"`
# a secas se resuelve contra el cwd, asi que fallaba en silencio en el caso
# documentado por el README: `.env` vive en la raiz del repo (junto a
# `.env.example` y `docker-compose.yml`) pero el backend se arranca desde
# `backend/`. El resultado no era un error visible sino algo peor -- los
# defaults de abajo coinciden con `.env.example`, asi que la app parecia
# funcionar mientras ignoraba cualquier valor que el usuario editara.
# Detectado validando el README desde un clon limpio (EVIDENCE.md E-12).
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    # Orden intencional: `backend/.env` se carga despues y por lo tanto pisa
    # al de la raiz, para permitir un override local sin tocar el compartido.
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://quoteflow:quoteflow@localhost:5432/quoteflow"

    llm_mode: Literal["fake", "real"] = "fake"
    # Proveedor del extractor real. Gemini primero: su plan gratuito basta
    # para una demo; si no responde, el grafo usa el extractor de reglas y lo
    # deja anotado en la auditoria (ver app/llm/fallback.py).
    llm_provider: Literal["gemini", "anthropic"] = "gemini"
    gemini_api_key: str = ""
    # Lite: la extraccion es corta y estructurada, y responde en ~2 s. En
    # pruebas (nov. 2026) gemini-flash-latest / 3.8-flash superaban los 60 s.
    gemini_model: str = "gemini-3.5-flash-lite"
    llm_timeout_seconds: float = 20.0
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"

    # Trazas en LangSmith (opcional). Apagadas por defecto: con ellas, el texto
    # del cliente sale hacia un servicio externo. Ver configure_tracing().
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "quoteflow"
    langsmith_endpoint: str = ""  # vacio = region por defecto (EE. UU.)

    app_env: str = "local"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_tracing(settings: Settings) -> bool:
    """Activa las trazas de LangSmith si la configuracion lo pide.

    La SDK de LangSmith (y LangGraph a traves de ella) lee `os.environ`, pero
    pydantic-settings carga `.env` sin copiarlo al entorno del proceso. Sin
    este paso, `LANGSMITH_TRACING=true` en `backend/.env` no tendria ningun
    efecto y nada lo avisaria.

    Devuelve True si las trazas quedaron activas. Sin key no se activan: una
    traza que no puede enviarse solo produce errores en segundo plano.
    """
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    return True
