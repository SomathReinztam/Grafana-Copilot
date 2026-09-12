.PHONY: help up fresh build down reset logs dev-infra dev-backend dev-frontend install

help:
	@echo "── Todo en Docker ──"
	@echo "make up      - construye y levanta TODO (grafana, renderer, backend, frontend)"
	@echo "make fresh   - reset total (down -v) y vuelve a levantar de cero"
	@echo "make down    - baja los contenedores (conserva el volumen)"
	@echo "make reset   - deja el dashboard de demo vacío (sin borrar nada más)"
	@echo "make logs    - sigue los logs de backend y frontend"
	@echo "── Modo dev (sin dockerizar la app) ──"
	@echo "make install / dev-infra / dev-backend / dev-frontend"

# --- Docker (todo el stack) ---
up:
	docker compose up -d --build

fresh:
	docker compose down -v && docker compose up -d --build

build:
	docker compose build

down:
	docker compose down

logs:
	docker compose logs -f backend frontend

reset:
	docker compose exec backend python -m app.reset_demo

# --- Modo dev (app en el host, solo Grafana en Docker) ---
install:
	cd backend && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
	cd frontend && npm install

dev-infra:
	docker compose up -d grafana renderer

dev-backend:
	cd backend && ./.venv/bin/uvicorn app.api:app --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev
