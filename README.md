# Grafana Copilot Agent

Un agente que vive junto a Grafana: ve tus paneles, investiga tus datos y construye/edita
dashboards reales sobre tu Postgres — con aprobación humana en cada escritura.

> Hackatón "Agents, Everywhere". Ver [`ARCHITECTURE.md`](./ARCHITECTURE.md) y [`PLAN.md`](./PLAN.md).

## Requisitos
- Docker + Docker Compose
- Python 3.12+, Node 20+
- Una API key de Gemini (`GOOGLE_API_KEY`)

## Quickstart

### 1. Base de datos de pruebas (northwind)
Corre en su propio compose (no incluido aquí). Debe quedar publicada en `localhost:5434`.

### 2. Grafana + image renderer
```bash
cp .env.example .env          # ajusta credenciales si quieres
docker compose up -d
# Grafana: http://localhost:3000  (admin/admin)
```
Verifica:
```bash
curl -s http://localhost:3000/api/health
curl -s -u admin:admin http://localhost:3000/api/datasources/uid/northwind-pg/health
# {"message":"Database Connection OK","status":"OK"}
```

### 3. Backend (agente) — Fase 1+
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # añade tu GOOGLE_API_KEY
```

### 4. Frontend (CopilotKit) — Fase 2+
_(pendiente)_

## Estructura
```
.
├── docker-compose.yaml         # Grafana (embedding + renderer) — Postgres NO va aquí
├── infra/provisioning/         # datasource Postgres (UID fijo: northwind-pg)
├── backend/
│   └── app/
│       ├── settings.py         # config por entorno
│       └── lib/                # toolkits reutilizados como librería
│           ├── postgres_toolkit.py       # SQL read-only
│           ├── grafana_helper.py         # REST: service acct, token, datasource, publish
│           └── grafana_panel_toolkit.py  # actuar sobre paneles vivos (read/write)
└── frontend/                   # web app React + CopilotKit (Fase 2)
```

## Estado
- [x] **Fase 0** — Infra: Grafana + renderer arriba, datasource conectando a northwind,
      render de panel a PNG verificado, toolkits como librería.
- [ ] Fase 1 — Backend: agente + analista SQL (texto).
- [ ] Fase 2 — Frontend CopilotKit + escritura con gate.
- [ ] Fase 3 — Vision (buffer de 5 imágenes).
- [ ] Fase 4 — Pulido + demo.

## Créditos / reutilización
Los toolkits (`postgres_toolkit`, `grafana_helper`, `grafana_panel_toolkit`) se reutilizan como
librería de proyectos previos y se limpiaron para este build. El core (superficie CopilotKit,
gate de aprobación, contexto vivo, vision) es net-new del hackatón.
