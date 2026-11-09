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
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"

    app_env: str = "local"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
