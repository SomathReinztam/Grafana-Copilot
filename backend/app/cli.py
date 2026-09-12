"""CLI para probar el agente end-to-end (Fase 1).

Uso:
  python -m app.cli                      # REPL interactivo
  python -m app.cli "¿qué tablas tiene mi BD?"   # una sola pregunta
"""
import sys
import uuid

from langchain_core.messages import HumanMessage

from app.agents.main_agent import create_main_agent
from app.common.llm import extract_text


def _ask(agent, config, text: str) -> str:
    result = agent.invoke({"messages": [HumanMessage(content=text)]}, config=config)
    return extract_text(result["messages"][-1])


def main() -> None:
    # Intenta conectar con Grafana para exponer tools de paneles (sin gate en CLI).
    dashboard_uid = grafana_url = grafana_token = ds_uid = ds_type = None
    try:
        from app.grafana_bootstrap import bootstrap_grafana

        grafana_url, grafana_token, dashboard_uid, ds_uid, ds_type = bootstrap_grafana()
        print(f"[Grafana conectado] dashboard uid={dashboard_uid} datasource={ds_uid}")
    except Exception as e:  # noqa: BLE001
        print(f"[Grafana no disponible: {e}] — sigo solo con análisis de datos.")

    agent = create_main_agent(
        dashboard_uid=dashboard_uid,
        grafana_url=grafana_url,
        grafana_token=grafana_token,
        datasource_uid=ds_uid,
        datasource_type=ds_type or "grafana-postgresql-datasource",
        gated=False,
    )
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    if len(sys.argv) > 1:  # one-shot
        print(_ask(agent, config, " ".join(sys.argv[1:])))
        return

    print("Grafana Copilot (Fase 1 CLI). Escribe tu mensaje; Ctrl-C para salir.")
    while True:
        try:
            user = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAdiós.")
            break
        if user:
            print("\n" + _ask(agent, config, user))


if __name__ == "__main__":
    main()
