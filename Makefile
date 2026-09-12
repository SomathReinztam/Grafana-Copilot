.PHONY: help infra backend frontend reset down install

help:
	@echo "make install   - instala deps de backend (venv) y frontend"
	@echo "make infra     - levanta Grafana + image-renderer (docker compose)"
	@echo "make backend   - corre el agente (FastAPI/AG-UI) en :8000"
	@echo "make frontend  - corre la web app (Next.js) en :3001"
	@echo "make reset     - deja el dashboard de demo vacío (para grabar)"
	@echo "make down      - baja los contenedores de Grafana"

install:
	cd backend && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
	cd frontend && npm install

infra:
	docker compose up -d

backend:
	cd backend && ./.venv/bin/uvicorn app.api:app --port 8000 --reload

frontend:
	cd frontend && npm run dev

reset:
	cd backend && ./.venv/bin/python -m app.reset_demo

down:
	docker compose down
