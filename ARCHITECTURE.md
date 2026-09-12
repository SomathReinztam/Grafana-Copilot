# Arquitectura — Grafana Copilot Agent

> Agente que vive junto a Grafana, ve tus paneles, investiga tus datos y construye/edita
> dashboards reales sobre tu Postgres — con aprobación humana en cada escritura.

---

## 1. Contexto y problema

### El tema del hackatón
> *"Agents are leaving the chatbox. Build an agent for a place people already work, talk, or
> live, then make it meaningfully more useful because of that context."*

El criterio que más pesa (Innovation & Theme Alignment) premia que **el entorno haga al
agente materialmente más capaz**, y castiga al agente que es "un chatbot genérico donde el
entorno es solo un envoltorio". La nota máxima es para el patrón *"cuyo valor central no
podría reproducirse en un chatbox".*

### El entorno elegido: Grafana
Grafana es donde los equipos de datos, analistas y operaciones **ya trabajan todo el día**.
Es un lugar de trabajo real, no una superficie inventada. Y tiene un problema real:

- Crear un dashboard sobre una base Postgres exige dominar **SQL** *y* la **estructura del
  JSON de paneles de Grafana** (datasource, `rawSql`, `fieldConfig`, tipos nativos...).
- Cuando un analista ve algo raro en un panel, tiene que **cambiar de contexto** a un cliente
  SQL para investigar, y luego volver a Grafana a traducir el hallazgo en un panel.
- El conocimiento de "qué gráficas valen la pena para estos datos" está en la cabeza de pocos.

### Nuestra propuesta
Un agente que **no vive en un chat aparte**, sino junto a Grafana (una web app con CopilotKit
que embebe los paneles **reales** de Grafana). El agente:

1. **Es consciente del contexto vivo** — sabe qué dashboard, paneles y rango de tiempo estás
   viendo *ahora* (vía `useCopilotReadable` de CopilotKit).
2. **Ve los paneles** — puede pedir la imagen renderizada de un panel e interpretarla
   visualmente (vision), con un buffer acotado de 5 imágenes que lo obliga a ser estratégico.
3. **Investiga tus datos** — delega el análisis profundo a subagentes analistas SQL que
   consultan tu Postgres de solo lectura.
4. **Actúa sobre el dashboard vivo** — crea, edita y borra paneles reales, y puede
   **recomendar y construir un dashboard desde cero**.
5. **Pide permiso** — toda escritura pasa por un *gate* de aprobación humana (human-in-the-loop
   real de CopilotKit), no por un prompt blando que el modelo pueda ignorar.

El arco de valor es **observe → diagnose → propose → approve → act**, nativo en el lugar donde
el trabajo ya ocurre.

### Por qué esto no se puede hacer en un chatbox
- El agente **ve el mismo dashboard que tú** y actúa sobre él; su salida *es* el dashboard que
  ya usas, no una respuesta de texto.
- El agente **mira el panel real renderizado** para diagnosticar.
- El resultado queda **persistido en Grafana**, listo para el resto del equipo.

---

## 2. Diferenciadores (para los jueces)

| # | Diferenciador | Criterio que ataca |
|---|---|---|
| 1 | Contexto vivo del dashboard (`useCopilotReadable`) | Innovation / Theme |
| 2 | Vision: el agente ve el panel real (buffer acotado de 5) | Innovation / Usefulness |
| 3 | Actúa sobre dashboards Grafana reales y persistentes | Core / Technical |
| 4 | Gate de aprobación humana en cada escritura | Usefulness (controllable) |
| 5 | Pool de analistas SQL paralelos (stretch) | Technical (orquestación) |
| 6 | CopilotKit (sponsor) como capa nativa in-app | Premio "Best Use of CopilotKit" |

---

## 3. Arquitectura de alto nivel

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NAVEGADOR                                                                 │
│  ┌───────────────────────────┐   ┌────────────────────────────────────┐  │
│  │  Web app (React)          │   │  Paneles Grafana REALES embebidos   │  │
│  │  + CopilotKit             │   │  (<iframe> d-solo / dashboard)      │  │
│  │  - chat del agente        │   │                                     │  │
│  │  - UI generativa del gate │   │  El agente escribe aquí → se        │  │
│  │  - useCopilotReadable ────┼───┼─► re-renderiza nativo                │  │
│  └─────────────┬─────────────┘   └────────────────────────────────────┘  │
└────────────────┼──────────────────────────────────────────────────────────┘
                 │ CopilotKit runtime (SSE)
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI + CopilotKit runtime + LangGraph)                        │
│                                                                           │
│  ┌──────────────────────── AGENTE PRINCIPAL (ReAct, Gemini) ───────────┐ │
│  │  Tools:                                                              │ │
│  │   · contexto      · grafana-read   · grafana-write (GATE) · vision   │ │
│  │   · invoke_data_analyst_1..5 ──────────────┐                         │ │
│  └────────────────────────────────────────────┼─────────────────────── ┘ │
│                                                │  custom tool node        │
│                                                ▼  (paralelo, stretch)     │
│           ┌─────────── SUBAGENTES ANALISTAS SQL (ReAct, Gemini) ────────┐ │
│           │  slot 1 .. slot 5, cada uno con su propio historial en state │ │
│           │  Tools: get_tables_names, get_tables_schemas, query_data_base │ │
│           └───────────────────────────────┬──────────────────────────────┘ │
└───────────────────────────────────────────┼──────────────────────────────┘
        │ REST (service acct token)          │ SQL read-only (SQLAlchemy)
        ▼                                     ▼
┌───────────────────────┐            ┌────────────────────────────┐
│  GRAFANA (docker)     │            │  POSTGRES DEL USUARIO      │
│  + image-renderer     │◄───────────│  (conectado en onboarding; │
│    (sidecar, vision)  │  datasource│   northwind para pruebas)  │
└───────────────────────┘            └────────────────────────────┘
```

---

## 4. Componentes

### 4.1 Frontend (React + CopilotKit)
- Chat del agente + **UI generativa** para el gate de aprobación (`renderAndWaitForResponse`).
- **Paneles Grafana reales embebidos** vía `<iframe>` a `d-solo` (requiere
  `GF_SECURITY_ALLOW_EMBEDDING=true` y acceso anónimo o token para el demo).
- **`useCopilotReadable`** empuja al agente: `dashboardUid`, lista de paneles
  (`id`, `title`, `type`), rango de tiempo actual, panel seleccionado.
- **Onboarding "conecta tu Postgres"**: el usuario ingresa su connection string → se valida
  → se introspecta el esquema → se activa el agente.

### 4.2 Backend (FastAPI + CopilotKit runtime + LangGraph)
- Implementa el stub de FastAPI que quedó pendiente en los repos de referencia.
- Expone el runtime de CopilotKit y monta el grafo de LangGraph del agente principal.
- Endpoint de onboarding: valida conexión Postgres e introspecta esquema.

### 4.3 Agente principal (LangGraph ReAct, Gemini)
- Orquesta. No consulta SQL directamente: delega en los analistas.
- Decide **crear un dashboard desde cero**, recomendarlo, o iterar panel por panel.
- Toda tool de escritura Grafana pasa por el gate.

### 4.4 Subagentes analistas SQL (LangGraph ReAct, Gemini)
- Especialistas en datos: introspección + queries de solo lectura (15 filas máx).
- Reutilizan `PostgresToolKit` (ya construido).
- Hasta **5 slots**, cada uno con su propio historial en el state (ver §6).

### 4.5 Grafana (docker) + image-renderer
- Se usa **la imagen de Grafana del usuario** (SunTalk) en el `docker-compose` final.
- Se añade el sidecar `grafana/grafana-image-renderer` para vision (§9).
- El datasource Postgres se **provisiona** (`provisioning/datasources/`) para que el agente
  tenga el **UID del datasource** al construir paneles.

### 4.6 Postgres del usuario
- **NO va en el docker-compose del proyecto**: la idea es que el usuario traiga su propia BD.
- Para pruebas se usa **northwind** (`postgres:postgres@localhost:5434/northwind`), que corre
  en su propio compose aparte.

---

## 5. Catálogo de tools

| Tier | Tool | Qué hace | Estado |
|---|---|---|---|
| **Contexto** | `get_current_dashboard_context` | Dashboard/paneles/rango vivo | 🆕 vía `useCopilotReadable` |
| Descubrir (read) | `get_db_tables_names`, `get_tables_schemas` | Tablas y DDL Postgres | ✅ `PostgresToolKit` |
| Analizar (read) | `query_data_base` | SELECT acotado, read-only | ✅ |
| Analizar (read) | `invoke_data_analyst_1..5` | Delega a subagente analista | ✅ patrón subgrafo-como-tool |
| Grafana leer (read) | `get_panels_summary`, `get_json_panel_by_id` | Inventario / JSON de paneles | ✅ `GrafanaPostgresToolKit` |
| **Grafana escribir** ⚠️ | `create_panel` | Añade panel al dashboard | ✅ → **envolver en gate** |
| **Grafana escribir** ⚠️ | `edit_json_panel` (JSONPath) | Edita campo de panel | ✅ → **gate** |
| **Grafana escribir** ⚠️ | `delete_panel` | Elimina panel | ✅ → **gate** |
| **Grafana escribir** ⚠️ | `create_dashboard` / `push_grafana_dashboard` | Publica dashboard nuevo | ✅ `GrafanaHelper` → **gate** |
| **Vision** | `look_at_panel(panel_id)` | Inyecta imagen del panel (buffer ≤5) | 🆕 (§9) |

⚠️ = escritura, siempre por el gate de aprobación humana.

**Descartado:** `DockerSandboxToolKit` (era para generar JSONL de A2UI; aquí no se necesita).
**Sin MCP:** se usa el toolkit REST propio (`GrafanaHelper` + `GrafanaPostgresToolKit`), que
da más control que las tools del MCP oficial.

---

## 6. Diseño del estado del grafo (historial)

Decisión: **el historial vive en el `state` del grafo LangGraph**, no en Postgres (los repos de
referencia lo guardaban en Postgres; aquí lo movemos al state + checkpointer).

```python
class AgentState(TypedDict):
    messages: list                      # conversación usuario ↔ agente principal
    dashboard_context: dict             # empujado desde el frontend (useCopilotReadable)
    db_conn: dict                       # datos de conexión tras el onboarding
    image_buffer: list                  # ≤5 refs de imágenes de panel vivas (§9)
    analyst_slots: dict                 # slots de analistas: { "1": {messages, status}, ... }
```

- **Persistencia entre turnos**: LangGraph `checkpointer` (para el hackatón, `MemorySaver`
  en memoria, con `thread_id` = sesión del usuario). Suficiente para el demo; migrable a
  checkpointer Postgres después si se quiere.
- **Historial main ↔ analista**: cada slot de `analyst_slots` guarda su propia lista de
  mensajes. Esto habilita que el agente principal decida:
  - **`mode="continue"`** → se anexa la nueva tarea al `messages` del slot (memoria).
  - **`mode="fresh"`** → se limpia el `messages` del slot y arranca conversación nueva.

---

## 7. Flujos del agente (escenarios de demo)

Ordenados de menor a mayor riesgo. Para el video (2 min) contar **1 → 3 → 4**.

**Flujo 1 — Explícame este dashboard (read-only).**
El agente lee todos los paneles y sus queries → resume qué mide → detecta huecos. Apertura
segura, cero escritura.

**Flujo 2 — ¿Qué pasa con este pico? (diagnóstico en contexto).**
Señalas un panel → el agente sabe cuál es → analista SQL hace drill-down → explica causa →
**propone** panel de desglose → gate → `create_panel` → se re-renderiza.

**Flujo 3 — Recomiéndame y construye un dashboard desde cero.**
Conectas tu Postgres → el analista explora los datos e idea gráficas → el agente principal
**recomienda un dashboard inicial** → gate → `create_dashboard`. (Flujo principal.)

**Flujo 4 — Ajusta este panel (edición quirúrgica + vision).**
"Cámbialo a barras" / "el umbral es 90" → el agente **mira el panel** (`look_at_panel`) para
confirmar → `edit_json_panel` por JSONPath → gate → cambia en vivo.

**Flujo 5 — Barrido proactivo (stretch).**
El agente escanea los paneles del rango actual y te avisa de anomalías antes de preguntar.

---

## 8. Vision — diseño del buffer de imágenes

**Objetivo**: que el agente vea el panel real, sin sobrecargar el contexto ni acumular
gráficas duplicadas/desactualizadas.

**Requisitos:**
1. **Modelo multimodal**: Gemini (`gemini-2.0-flash` / `2.5`). ⚠️ `gpt-oss-120b` NO tiene visión.
2. **Render server-side**: sidecar `grafana/grafana-image-renderer`. El endpoint
   `/render/d-solo/<uid>?panelId=X&from=...&to=...&width=...&height=...` produce el PNG.
   (Capturar el iframe con html2canvas NO sirve: es cross-origin.)

**Mecanismo (buffer acotado, auto-gestionado):**
- La tool `look_at_panel(panel_id)` entrega la imagen como **tool result** (vía nativa que las
  APIs sí soportan; NO se puede meter imagen en el rol `system` en Anthropic/OpenAI).
- Un **paso de desalojo** en el grafo mantiene ≤5 imágenes vivas: al superar 5, o al re-mirar
  un panel ya presente, se **reemplaza la imagen vieja por un stub de texto**
  (`[imagen del panel "Ventas" desalojada]`), preservando el par `tool_call`/`tool_result`.
- Resultado: tope duro de 5 (obliga a mirar estratégico), sin duplicados/stale, y compatible
  con la API.

---

## 9. Multi-analista paralelo (STRETCH — fase final)

**Objetivo**: el agente principal puede invocar hasta 5 analistas y ejecutarlos **en paralelo**,
y decidir por cada uno si continúa su conversación o arranca de cero.

**Diseño:**
- **5 tools nominales** `invoke_data_analyst_1..5`, cada una con args `task: str` y
  `mode: "continue" | "fresh"`. (Modelo mental claro; alternativa: 1 tool con `slot_id`.)
- **Custom tool node**: cuando el agente principal emite varias de estas tool calls en un
  mismo turno, el nodo las ejecuta concurrentemente con `asyncio.gather`, cada una invocando
  el subgrafo analista con el historial del slot (continue) o uno nuevo (fresh), y devuelve un
  `ToolMessage` por cada una.
- Extiende el patrón "subgrafo-como-tool" que ya existe (se intercepta la tool call por nombre
  antes del `ToolNode` estándar).

Se deja para el final: primero el core con **un** analista secuencial.

---

## 10. Gotchas técnicos

- **Gemini + LangChain devuelve contenido como lista de dicts** (con texto y a veces una
  *firma*/signature en tool calls o thinking). NO asumir `msg.content` como `str`. Usar un
  helper robusto:
  ```python
  def extract_text(msg) -> str:
      c = msg.content
      if isinstance(c, str):
          return c
      parts = []
      for p in c:                      # lista de dicts
          if isinstance(p, dict) and p.get("type") == "text":
              parts.append(p.get("text", ""))
          elif isinstance(p, str):
              parts.append(p)
      return "".join(parts)
  ```
  Para tool calls usar `msg.tool_calls` (LangChain los normaliza), no parsear el content.
- **Grafana embedding**: `GF_SECURITY_ALLOW_EMBEDDING=true` y acceso anónimo (o token) para
  que el iframe cargue. Posible `GF_SECURITY_COOKIE_SAMESITE=none`.
- **Image renderer**: `GF_RENDERING_SERVER_URL=http://renderer:8081/render` y
  `GF_RENDERING_CALLBACK_URL=http://grafana:3000/`.
- **Datasource UID**: el agente necesita el UID del datasource Postgres para construir paneles.
  Provisionarlo (`provisioning/datasources/`) y leerlo por API.
- **Credenciales**: los repos de referencia tienen secretos commiteados en claro. En el repo
  nuevo, todo por `.env` (git-ignored) y rotar lo que se haya expuesto.

---

## 11. Elegibilidad del hackatón

Las reglas exigen que el proyecto y su **funcionalidad central** se construyan durante el
evento; los building blocks pre-existentes se permiten como librerías.

- **Repo nuevo, público, con historial de commits de hoy.**
- **Net-new hoy**: superficie CopilotKit + `useCopilotReadable`, gate de aprobación,
  `get_current_dashboard_context`, tool de vision + buffer, cableado FastAPI+CopilotKit+LangGraph,
  (stretch) tool node paralelo.
- **Reutilizado como librería**: `PostgresToolKit`, `GrafanaHelper`, `GrafanaPostgresToolKit`,
  pipeline planner→analyst→dashboard, patrón subgrafo-como-tool.

---

## 12. Fuera de alcance (por tiempo)

- Plugin nativo de Grafana (stretch mayor; la web app embebida es el camino de hoy).
- A2UI (compite con el render nativo de Grafana; descartado para este proyecto).
- Datasources no-Postgres (Prometheus/Loki).
- Checkpointer Postgres / multi-usuario / auth robusta.
