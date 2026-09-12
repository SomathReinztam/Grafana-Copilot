"""Agente principal (Grafana Copilot).

Orquesta: delega el análisis de datos al subagente analista (patrón analista-como-tool) y,
cuando hay credenciales de Grafana, expone tools de lectura sobre el dashboard vivo.
El historial usuario<->agente vive en el state del grafo (MemorySaver).
"""
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from sqlalchemy.engine import Engine

from app.agents.analyst import create_analyst_agent
from app.agents.gate import gated_tool
from app.common.db import make_engine
from app.common.llm import extract_text, make_llm
from app.lib.grafana_panel_toolkit import GrafanaPanelToolKit
from app.prompts import MAIN_SYSTEM_PROMPT


class _AnalystArgs(BaseModel):
    task: str = Field(
        description="Tarea de análisis de datos, clara y específica, en lenguaje natural."
    )


def _build_invoke_analyst_tool(analyst) -> StructuredTool:
    def _invoke(task: str) -> str:
        try:
            result = analyst.invoke({"messages": [HumanMessage(content=task)]})
            return extract_text(result["messages"][-1])
        except Exception as e:  # noqa: BLE001
            return f"El analista de datos falló: {e}"

    return StructuredTool.from_function(
        name="invoke_data_analyst",
        description=(
            "Delega una tarea de análisis de datos al analista SQL (explora la BD, ejecuta "
            "consultas de solo lectura, propone gráficas). Pásale una tarea clara en lenguaje natural."
        ),
        func=_invoke,
        args_schema=_AnalystArgs,
    )


def create_main_agent(
    engine: Engine | None = None,
    dashboard_uid: str | None = None,
    grafana_url: str | None = None,
    grafana_token: str | None = None,
    datasource_uid: str | None = None,
    datasource_type: str = "grafana-postgresql-datasource",
    gated: bool = False,
    use_checkpointer: bool = True,
):
    """Construye el grafo del agente principal.

    - gated=True: las tools de escritura pasan por el gate de aprobación (interrupt).
      Úsalo al servir por FastAPI/CopilotKit. En CLI conviene gated=False.
    - use_checkpointer: MemorySaver para persistir el historial en el state.
    """
    engine = engine or make_engine()
    llm = make_llm()

    analyst = create_analyst_agent(engine=engine, llm=llm)
    tools = [_build_invoke_analyst_tool(analyst)]

    # Tools sobre el dashboard vivo (si hay credenciales de Grafana).
    if dashboard_uid and grafana_url and grafana_token:
        panel_kit = GrafanaPanelToolKit(
            grafana_url,
            grafana_token,
            dashboard_uid,
            engine,
            datasource_uid=datasource_uid,
            datasource_type=datasource_type,
        )
        tools += panel_kit.read_tools()
        write_tools = panel_kit.write_tools()
        tools += [gated_tool(t) for t in write_tools] if gated else write_tools

    return create_react_agent(
        llm,
        tools,
        prompt=MAIN_SYSTEM_PROMPT,
        checkpointer=MemorySaver() if use_checkpointer else None,
    )
