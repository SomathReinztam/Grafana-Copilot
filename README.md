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

## Quickstart (todo en Docker)
Requisitos: Docker, una API key de Gemini. (La BD del usuario va aparte; para pruebas,
northwind publicado en `localhost:5434` con su propio compose.)
```bash
cp .env.example .env            # pon tu GOOGLE_API_KEY en .env
make up                         # construye y levanta grafana + renderer + backend + frontend
# abre  http://localhost:3001   (Grafana en :3000, agente en :8000)

make fresh                      # reset TOTAL: down -v y levanta de cero (dashboard limpio)
make down                       # baja los contenedores (conserva el volumen)
make reset                      # solo vacía el dashboard de demo
```
`docker compose down -v` borra únicamente el volumen de Grafana; el bootstrap del backend
recrea token, dashboard y datasource al levantar. Tu Postgres (otro compose) no se toca.

### Modo dev (app en el host, solo Grafana en Docker)
```bash
make install                    # venv backend + npm frontend
make dev-infra                  # grafana + renderer
echo "GOOGLE_API_KEY=..." >> backend/.env
make dev-backend                # :8000
make dev-frontend               # :3001
```

## Qué se construyó durante el hackathon (elegibilidad)
- **Net-new hoy**: superficie CopilotKit + `useCopilotReadable` (contexto vivo), endpoint
  AG-UI, gate de aprobación (`interrupt`), `create_panel_from_spec`, **visión**
  (`look_at_panel` + buffer de 5 imágenes), cableado FastAPI + LangGraph + Next.js.
- **Reutilizado como librería** (limpiado): clientes REST de Grafana y toolkit SQL de
  proyectos previos (`backend/app/lib/`).

## Estado
Fases 0–3 completas y verificadas end-to-end. Ver [`PLAN.md`](./PLAN.md).
