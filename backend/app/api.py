"""Servidor FastAPI que expone el agente por el protocolo AG-UI (nativo).

Arranque:
  cd backend && ./.venv/bin/uvicorn app.api:app --reload --port 8000

El frontend (react-core 1.71 = AG-UI) se conecta a POST /agui con @ag-ui/client HttpAgent.
"""
import logging

from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_langgraph import LangGraphAgent as AGUILangGraphAgent
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.agents.main_agent import create_main_agent
from app.common.db import make_engine
from app.grafana_bootstrap import bootstrap_grafana

logger = logging.getLogger("grafana-copilot")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Grafana Copilot Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

STATE: dict = {"dashboard_uid": None, "grafana_url": None}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", **STATE}


def _build_agui_agent():
    engine = make_engine()
    grafana_url, token, dash_uid, ds_uid, ds_type = bootstrap_grafana()
    STATE["dashboard_uid"] = dash_uid
    STATE["grafana_url"] = grafana_url
    logger.info("Grafana bootstrap OK — dashboard uid=%s datasource=%s", dash_uid, ds_uid)
    graph = create_main_agent(
        engine=engine,
        dashboard_uid=dash_uid,
        grafana_url=grafana_url,
        grafana_token=token,
        datasource_uid=ds_uid,
        datasource_type=ds_type or "grafana-postgresql-datasource",
        gated=True,  # las escrituras pasan por el gate (interrupt AG-UI)
    )
    return AGUILangGraphAgent(name="grafana_copilot", graph=graph)


_agui_agent = _build_agui_agent()


@app.post("/agui")
async def agui(input: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))

    async def event_stream():
        async for event in _agui_agent.run(input):
            yield encoder.encode(event)

    return StreamingResponse(event_stream(), media_type=encoder.get_content_type())
