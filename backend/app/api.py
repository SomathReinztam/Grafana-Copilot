"""Servidor FastAPI que expone el agente vía CopilotKit (protocolo AG-UI).

Arranque:
  cd backend && ./.venv/bin/uvicorn app.api:app --reload --port 8000

El frontend (Fase 2) apunta su CopilotKit runtime a /copilotkit.
"""
import logging

from fastapi import FastAPI

from app.agents.main_agent import create_main_agent
from app.common.db import make_engine
from app.grafana_bootstrap import bootstrap_grafana

logger = logging.getLogger("grafana-copilot")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Grafana Copilot Agent")

# Contexto compartido del arranque (para el frontend y debugging)
STATE: dict = {"dashboard_uid": None, "grafana_url": None}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", **STATE}


def _build_graph():
    engine = make_engine()
    grafana_url, token, dash_uid = bootstrap_grafana()
    STATE["dashboard_uid"] = dash_uid
    STATE["grafana_url"] = grafana_url
    logger.info("Grafana bootstrap OK — dashboard uid=%s", dash_uid)
    # gated=True: las escrituras pasan por el gate de aprobación (interrupt)
    return create_main_agent(
        engine=engine,
        dashboard_uid=dash_uid,
        grafana_url=grafana_url,
        grafana_token=token,
        gated=True,
    )


# Registrar el agente en CopilotKit
try:
    from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
    from copilotkit.integrations.fastapi import add_fastapi_endpoint

    _graph = _build_graph()
    _sdk = CopilotKitRemoteEndpoint(
        agents=[
            LangGraphAGUIAgent(
                name="grafana_copilot",
                description="Agente que construye y edita dashboards de Grafana sobre Postgres.",
                graph=_graph,
            )
        ]
    )
    add_fastapi_endpoint(app, _sdk, "/copilotkit")
    logger.info("CopilotKit endpoint montado en /copilotkit")
except Exception:  # noqa: BLE001
    logger.exception("No se pudo montar el endpoint de CopilotKit")
