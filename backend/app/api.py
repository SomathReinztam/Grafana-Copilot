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
    # recursion_limit alto: construir un dashboard completo hace muchas tool calls
    return AGUILangGraphAgent(
        name="grafana_copilot", graph=graph, config={"recursion_limit": 100}
    )


_agui_agent = _build_agui_agent()


def _sanitize_messages(messages: list):
    """Quita tool_calls sin su ToolMessage (y resultados huérfanos). Un run que falla a
    mitad deja el historial del cliente inconsistente; sin esto, el siguiente mensaje
    revienta con 'AIMessages with tool_calls that do not have a corresponding ToolMessage'."""
    result_ids = {
        m.tool_call_id
        for m in messages
        if getattr(m, "role", None) == "tool" and getattr(m, "tool_call_id", None)
    }
    call_ids = set()
    for m in messages:
        if getattr(m, "role", None) == "assistant":
            for tc in getattr(m, "tool_calls", None) or []:
                call_ids.add(tc.id)

    cleaned = []
    for m in messages:
        role = getattr(m, "role", None)
        if role == "assistant" and getattr(m, "tool_calls", None):
            kept = [tc for tc in m.tool_calls if tc.id in result_ids]
            if kept:
                cleaned.append(m.model_copy(update={"tool_calls": kept}))
            elif (getattr(m, "content", None) or "").strip():
                cleaned.append(m.model_copy(update={"tool_calls": None}))
            # si no hay ni resultado ni texto → se descarta el mensaje
        elif role == "tool":
            if getattr(m, "tool_call_id", None) in call_ids:
                cleaned.append(m)  # descarta resultados huérfanos
        else:
            cleaned.append(m)
    return cleaned


@app.post("/agui")
async def agui(input: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))
    input = input.model_copy(update={"messages": _sanitize_messages(input.messages)})

    async def event_stream():
        async for event in _agui_agent.run(input):
            yield encoder.encode(event)

    return StreamingResponse(event_stream(), media_type=encoder.get_content_type())
