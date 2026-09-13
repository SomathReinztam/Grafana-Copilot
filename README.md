# Grafana Copilot Agent

**An AI agent that lives inside Grafana** — it reads your data, understands the dashboard
you're looking at, sees your panels, and builds or edits real visualizations, with human
approval on every change.

> Built for the *Agents, Everywhere* hackathon — "agents leaving the chatbox." The chosen
> environment is **Grafana**, where data and operations teams already work. The agent isn't a
> separate chatbot: it shows up next to your dashboards, understands the one you're viewing,
> and acts on it.

## Why the environment matters
This is not a chatbot with Grafana bolted on. Its core value **cannot be reproduced in a
standalone chatbox**:
- **Live context** — the agent knows which dashboard, panels, and time range you're viewing
  right now (`useCopilotReadable`).
- **Vision** — it can *see* the actually-rendered panel (as an image) and diagnose it visually
  (trends, gaps, misconfigured axes), not just read SQL.
- **Real action** — it creates and edits panels on the live dashboard via Grafana's REST API,
  so its output *is* the dashboard your team already uses, persisted for everyone.
- **Human in the loop** — every edit/delete goes through an approval gate; you stay in control.

## Architecture
```
Browser
  ├─ Next.js + CopilotKit (chat + approval gate)   ── AG-UI ──►  FastAPI backend
  └─ REAL Grafana dashboard embedded (iframe)                     ├─ Main agent (LangGraph · Gemini)
        ▲  useCopilotReadable → live context                      │    ├─ SQL analyst subagent
        │                                                         │    ├─ Grafana tools (create/edit, gated)
        └──── the agent writes here; it re-renders ◄──────────────┘    └─ look_at_panel (vision, 5-image buffer)
                                             REST + image-renderer ▲          │ read-only SQL
                                       Grafana (Docker) ───────────┘          ▼
                                                                       User's PostgreSQL
```
See [`COMO_FUNCIONA.md`](./COMO_FUNCIONA.md) for a deeper walkthrough (with sequence diagrams),
[`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full design, and [`PLAN.md`](./PLAN.md) for the
build plan.

## Stack
- **Backend**: Python, FastAPI, LangGraph, Google Gemini (`gemini-3.8-flash`), SQLAlchemy.
  Native **AG-UI** protocol (`ag-ui-langgraph`).
- **Frontend**: Next.js + **CopilotKit** (`@copilotkit/react-core`) + `@ag-ui/client`.
- **Infra**: Grafana + `grafana-image-renderer` (Docker). The user's own PostgreSQL
  (for the demo: Northwind — see below).

## Quickstart (everything in Docker)
Requirements: Docker and a Google Gemini API key.
```bash
# 1) Sample database (Northwind) on localhost:5434
docker compose -f example-db/docker-compose.yml up -d

# 2) The whole stack: Grafana + renderer + backend + frontend
cp .env.example .env            # set GOOGLE_API_KEY in .env
make up                         # = docker compose up -d --build
# open  http://localhost:3001   (Grafana on :3000, agent on :8000)

make fresh                      # FULL reset: down -v then up (clean dashboard)
make down                       # stop containers (keeps the volume)
make reset                      # just empty the demo dashboard
```
`docker compose down -v` only removes Grafana's volume; the backend bootstrap recreates the
service-account token, the dashboard, and the datasource on startup. Your PostgreSQL (a
separate compose) is never touched.

### Dev mode (app on the host, only Grafana in Docker)
```bash
make install                    # backend venv + frontend npm
make dev-infra                  # grafana + renderer
echo "GOOGLE_API_KEY=..." >> backend/.env
make dev-backend                # :8000
make dev-frontend               # :3001
```

## Test database (Northwind)
The agent works over any PostgreSQL database. For the demo it uses the classic **Northwind**
sample dataset, kept in [`example-db/`](./example-db) and run as its own compose (in real use,
the user brings their own database):
- **Image**: `postgres:15`
- **Seed**: [`example-db/northwind.sql`](./example-db/northwind.sql) — auto-loaded on first
  start via `/docker-entrypoint-initdb.d`.
- **Exposed at**: `localhost:5434` (user `postgres`, password `postgres`, db `northwind`).

```bash
docker compose -f example-db/docker-compose.yml up -d      # start
docker compose -f example-db/docker-compose.yml down -v    # remove (and its data)
```
Grafana reaches this DB via `host.docker.internal:5434` (provisioned datasource in
`infra/provisioning/`), and the agent's SQL analyst connects through SQLAlchemy (read-only).

## Built during the hackathon (eligibility)
- **Net-new**: the CopilotKit + AG-UI integration, `useCopilotReadable` live context, the
  approval gate (LangGraph interrupts), `create_panel_from_spec`, the **vision** capability
  (`look_at_panel` + bounded 5-image buffer), the FastAPI + LangGraph + Next.js wiring, and the
  full Docker setup.
- **Reused as libraries** (cleaned up): generic Grafana REST and SQL utilities from prior
  personal projects, under `backend/app/lib/`.

## Repository
https://github.com/SomathReinztam/Grafana-Copilot

## Youtube
https://www.youtube.com/watch?v=byMte-KQTAw

