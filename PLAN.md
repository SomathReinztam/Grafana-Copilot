# Plan de build — 4 horas (Grafana Copilot Agent)

Ventana: **11:15 – 15:30** (build) · **15:30 – 16:00** (submission). ~4h de código.
Estrategia: **thin slice primero** (algo end-to-end funcionando cuanto antes), features encima.
Ver `ARCHITECTURE.md` para el detalle de diseño.

---

## Regla de oro
Al final de cada fase debe haber **algo demostrable**. Si una fase se atrasa, se corta su
alcance, no se salta la siguiente. Vision y multi-analista son **capas encima**, no bloqueantes.

---

## Fase 0 — Setup e infra ✅ COMPLETA  · *DoD: Grafana arriba + northwind + un panel renderiza*
- [x] Repo nuevo, git init (commits de hoy → elegibilidad). *(commit pendiente de tu OK)*
- [x] Estructura: `frontend/`, `backend/app/lib`, `infra/provisioning`.
- [x] `docker-compose.yaml` = imagen Grafana + sidecar `grafana-image-renderer`. (Postgres NO va aquí.)
- [x] Env Grafana: embedding + anónimo + rendering + `RENDERER_TOKEN` (requerido en prod).
- [x] northwind arriba (`localhost:5434`, 14 tablas). Datasource provisionado (UID fijo `northwind-pg`),
      health = "Database Connection OK".
- [x] Toolkits como librería (limpios, sin secretos): `postgres_toolkit`, `grafana_helper`,
      `grafana_panel_toolkit`. `.env`/`.env.example` en root y backend.
- [x] Verificado: `/api/health` OK, datasource conecta, **render de panel a PNG con datos reales OK**.

## Fase 1 — Backend core: agente + 1 analista, solo texto ✅ COMPLETA  · *DoD: conversación end-to-end*
- [x] Grafo LangGraph del agente principal (Gemini `gemini-3.8-flash`) — probado por CLI.
      *(FastAPI + runtime CopilotKit → movido a Fase 2, se cablea con el frontend.)*
- [x] Helper `extract_text()` para el contenido lista-de-dicts de Gemini.
- [x] Tools read de Grafana (`get_panels_summary`, `get_json_panel_by_id`) listas para
      enchufar cuando haya token. *(`get_current_dashboard_context` → Fase 2, necesita frontend.)*
- [x] Subagente analista (1 slot, secuencial) con `PostgresToolKit` + `invoke_data_analyst`.
- [x] Historial en el state del grafo + `MemorySaver` (thread_id = sesión).
- [x] Probado: "¿qué tablas...?" → delega al analista → consulta northwind (14 tablas, 830 órdenes).

## Fase 2 — Frontend + escritura con gate (≈60 min)  · *DoD: crear/editar panel real con aprobación*
- [ ] Web app React + CopilotKit, chat conectado al backend.
- [ ] Embeber un dashboard/paneles Grafana reales (`<iframe>` d-solo).
- [ ] `useCopilotReadable` → contexto vivo real hacia `get_current_dashboard_context`.
- [ ] Tools write con **gate** (`renderAndWaitForResponse`): `create_panel`, `edit_json_panel`,
      `delete_panel`, `create_dashboard`.
- [ ] Probar **Flujo 3**: conectar BD → recomendar dashboard → aprobar → se crea en Grafana.

## Fase 3 — Vision (≈45 min)  · *DoD: el agente ve un panel y lo usa para editar*
- [ ] Tool `look_at_panel(panel_id)` → PNG del renderer como tool result.
- [ ] Paso de desalojo: buffer ≤5, reemplaza imagen vieja por stub de texto.
- [ ] Confirmar modelo Gemini multimodal en el agente principal.
- [ ] Probar **Flujo 4**: "ajústame este panel" → mira → propone → gate → edita.

## Fase 4 — Pulido + demo (≈30 min)  · *DoD: demo de 2 min ensayada*
- [ ] Sembrar escenario reproducible (dashboard + datos northwind).
- [ ] Ensayar arco **1 → 3 → 4** (entender → construir → ajustar con vision).
- [ ] Arreglar rough edges visibles. README con setup + qué es net-new.

## Fase STRETCH — Multi-analista paralelo (si sobra tiempo)
- [ ] 5 tools `invoke_data_analyst_1..5` con `task` + `mode: continue|fresh`.
- [ ] Custom tool node con `asyncio.gather` para correr slots en paralelo.
- [ ] Slots con historial propio en `analyst_slots` (continue vs fresh).

---

## Submission (15:30 – 16:00) — NO dejar para el final
- [ ] Título + descripción escrita.
- [ ] Repo público (limpio, README, sin secretos).
- [ ] Video de 2 min (arco 1→3→4; mostrar el gate y la vision).
- [ ] Post en redes etiquetando a los partners.
- [ ] Enviar en el portal **antes** del deadline.

## Reparto sugerido (si son varios)
- **A — Infra/Backend**: Fase 0 + agente/analista + tools (LangGraph).
- **B — Frontend**: CopilotKit + embed Grafana + gate UI + `useCopilotReadable`.
- **C — Vision/Demo**: renderer + `look_at_panel` + buffer + guion y video.

## Riesgos y cortes
- **Embedding de Grafana no carga** → fallback: capturas/paneles d-solo con anónimo forzado.
- **Vision se atrasa** → es capa 2, se corta; el core (Fases 1–2) ya es un demo válido.
- **Gemini content lista-de-dicts** → helper `extract_text()` desde el minuto uno.
- **CopilotKit human-in-the-loop** → si el `renderAndWaitForResponse` da guerra, gate mínimo
  con un botón aprobar/rechazar en React plano (pierde algo de "wow", conserva el control).
