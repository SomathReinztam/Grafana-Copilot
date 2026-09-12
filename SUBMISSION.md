# Submission — Grafana Copilot Agent

Material listo para pegar en el portal del hackathon.

## Título (elige uno)
- **Grafana Copilot** — an agent that lives in your dashboards
- **PanelPilot** — the agent that sees and builds your Grafana
- **Grafana Copilot: dashboards that build themselves, with you in the loop**

## Descripción escrita (para el portal)
> Grafana Copilot es un agente que vive **dentro de Grafana**, el lugar donde los equipos de
> datos y operaciones ya trabajan. En lugar de un chatbot separado, aparece junto a tus
> dashboards: sabe cuál estás viendo, **ve los paneles realmente renderizados** para
> diagnosticar visualmente (tendencias, ejes mal configurados, huecos), investiga tu base de
> datos Postgres con un subagente SQL, y **crea y edita paneles reales** — con un gate de
> aprobación humana en cada escritura. Su salida no es texto: es el dashboard que tu equipo ya
> usa. Construido con CopilotKit (AG-UI), LangGraph + Gemini, y el image-renderer de Grafana
> para darle visión al agente. Es un valor que un chatbox no puede reproducir: el agente ve y
> actúa donde el trabajo ya ocurre.

## Guion de demo (2 minutos)
Antes de grabar: `make reset` (dashboard vacío) y ten los 3 servicios arriba. Abre
`http://localhost:3001`.

- **0:00–0:15 — El entorno.** "Esto es Grafana, donde los equipos de datos ya viven. El
  agente vive aquí mismo." Muestra la app: dashboard embebido + barra "Grafana Copilot".
- **0:15–0:20 — Contexto vivo.** Menciona: "el agente ya sabe qué dashboard y datos estoy
  viendo." (útil si preguntas algo del dashboard actual).
- **0:20–1:00 — Construir con aprobación.** Escribe:
  > *"Recomiéndame y crea un dashboard inicial de ventas para esta base de datos."*
  El agente delega en el analista SQL → propone paneles → aparece el **gate 🔐 Aprobación
  requerida** → **Aprobar** → los paneles se crean y aparecen en vivo. Enfatiza el gate
  (human-in-the-loop) y que son paneles reales de Grafana.
- **1:00–1:40 — Visión (el "wow").** Escribe:
  > *"Mira el panel de órdenes por mes y dime qué mejorarías."*
  El agente usa `look_at_panel`, **ve la imagen** y responde con un diagnóstico visual real
  (p. ej., que el rango de tiempo está desajustado y los datos quedan comprimidos). Recalca:
  "esto no sale del SQL — el agente está viendo el panel."
- **1:40–2:00 — Cierre.** "Un agente nativo de Grafana: ve lo que tú ves, actúa sobre tus
  dashboards reales, y siempre con tu aprobación. Valor que no cabe en un chatbox."

## Post para redes (borrador)
> 🚀 Construimos **Grafana Copilot** en el hackathon *Agents, Everywhere*: un agente que vive
> DENTRO de Grafana. Ve tus paneles renderizados 👀, investiga tu Postgres y construye/edita
> dashboards reales — con aprobación humana en cada paso.
> Los agentes salieron del chatbox. 📊🤖
> Construido con @CopilotKit (AG-UI), LangGraph + Gemini y Grafana.
> #AgentsEverywhere  [+ etiquetar a los partners del evento]

_(Ajusta los handles/menciones a los partners que pida el hackathon: CopilotKit, OpenAI, Exa,
Auth0, etc.)_

## Checklist de envío
- [ ] Título
- [ ] Descripción escrita
- [ ] Repo público de GitHub (sin secretos — `.env` está en `.gitignore`)
- [ ] Video de 2 min (guion arriba)
- [ ] Post en redes etiquetando a los partners
- [ ] Enviar en el portal antes del deadline
