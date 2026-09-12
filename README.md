# Grafana Copilot Agent

**Un agente que vive dentro de Grafana** — ve tus paneles, investiga tus datos y
construye/edita dashboards reales sobre tu Postgres, con aprobación humana en cada escritura.

> Hackathon *Agents, Everywhere* — "los agentes salen del chatbox". El entorno elegido es
> **Grafana**, donde los equipos de datos y operaciones ya trabajan. Aquí el agente no es un
> chat aparte: aparece junto a tus dashboards, entiende el que estás viendo y actúa sobre él.

## Por qué encaja con el tema
No es un chatbot con Grafana pegado. El valor **no se puede reproducir en un chatbox**:
- **Contexto vivo**: el agente sabe qué dashboard, paneles y rango de tiempo estás viendo
  (`useCopilotReadable`).
- **Visión**: puede *ver* el panel realmente renderizado (imagen) y diagnosticar tendencias,
  huecos o ejes mal configurados — no solo leer SQL.
- **Acción real**: crea y edita paneles del dashboard vivo; su salida *es* el dashboard que
  ya usas, persistido para todo el equipo.
- **Control humano**: toda escritura pasa por un gate de aprobación (human-in-the-loop real).

## Arquitectura
```
Navegador
  ├─ Next.js + CopilotKit (chat + gate de aprobación)   ── AG-UI ──►  Backend FastAPI
  └─ Paneles Grafana REALES embebidos (iframe)                         ├─ Agente principal (LangGraph, Gemini)
        ▲  useCopilotReadable → contexto vivo                          │    ├─ subagente analista SQL
        │                                                              │    ├─ tools Grafana (crear/editar, gated)
        └──────── el agente escribe aquí, se re-renderiza ◄────────────┘    └─ look_at_panel (visión, buffer de 5)
                                                     REST + image-renderer ▲        │ SQL read-only
                                            Grafana (Docker) ──────────────┘        ▼
                                                                            Postgres del usuario
```
Detalle completo en [`ARCHITECTURE.md`](./ARCHITECTURE.md); plan de build en [`PLAN.md`](./PLAN.md).

## Stack
- **Backend**: Python, FastAPI, LangGraph, Gemini (`gemini-3.8-flash`), SQLAlchemy.
  Protocolo **AG-UI** (`ag-ui-langgraph`).
- **Frontend**: Next.js + **CopilotKit** (`@copilotkit/react-core`) + `@ag-ui/client`.
- **Infra**: Grafana + `grafana-image-renderer` (Docker). Postgres del usuario (demo: northwind).

## Quickstart
Requisitos: Docker, Python 3.12+, Node 20+, una API key de Gemini.
```bash
# 0) base de datos de prueba (northwind) publicada en localhost:5434 (su propio compose)

# 1) infra Grafana + renderer
cp .env.example .env
make infra                      # http://localhost:3000 (admin/admin)

# 2) backend (agente)
make install                    # venv + deps de backend y frontend
echo "GOOGLE_API_KEY=..." >> backend/.env
make backend                    # http://localhost:8000

# 3) frontend
make frontend                   # http://localhost:3001

# limpiar el dashboard para grabar la demo:
make reset
```

## Qué se construyó durante el hackathon (elegibilidad)
- **Net-new hoy**: superficie CopilotKit + `useCopilotReadable` (contexto vivo), endpoint
  AG-UI, gate de aprobación (`interrupt`), `create_panel_from_spec`, **visión**
  (`look_at_panel` + buffer de 5 imágenes), cableado FastAPI + LangGraph + Next.js.
- **Reutilizado como librería** (limpiado): clientes REST de Grafana y toolkit SQL de
  proyectos previos (`backend/app/lib/`).

## Estado
Fases 0–3 completas y verificadas end-to-end. Ver [`PLAN.md`](./PLAN.md).
