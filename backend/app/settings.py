"""Configuración central del backend. Lee de entorno / .env (nada hardcodeado)."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # Grafana (visto desde el backend, que corre en el host)
    grafana_url: str = "http://localhost:3000"
    grafana_admin_user: str = "admin"
    grafana_admin_password: str = "admin"

    # Base de datos del usuario (default: northwind de pruebas)
    db_host: str = "localhost"
    db_port: str = "5434"
    db_user: str = "postgres"
    db_pass: str = "postgres"
    db_name: str = "northwind"

    # LLM
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    @property
    def db_conn_string(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
