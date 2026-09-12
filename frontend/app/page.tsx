"use client";

import { useEffect, useState } from "react";
import { useCopilotReadable, useLangGraphInterrupt } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";

const GRAFANA_URL =
  process.env.NEXT_PUBLIC_GRAFANA_URL || "http://localhost:3000";
const DASH_UID = process.env.NEXT_PUBLIC_DASHBOARD_UID || "copilot-main";

type Panel = { id: number; title: string; type: string };
type Ctx = {
  dashboardUid: string;
  title?: string;
  timeRange?: unknown;
  panels: Panel[];
};

export default function Home() {
  const [ctx, setCtx] = useState<Ctx>({ dashboardUid: DASH_UID, panels: [] });

  // Contexto vivo del dashboard (poll cada 4s).
  useEffect(() => {
    const refresh = async () => {
      try {
        const r = await fetch("/api/context");
        if (r.ok) setCtx(await r.json());
      } catch {
        /* noop */
      }
    };
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, []);

  // El agente "ve" lo que el usuario está viendo (diferenciador vs chatbox).
  useCopilotReadable({
    description:
      "Dashboard de Grafana que el usuario está viendo AHORA: uid, título, rango de tiempo y paneles (id, título, tipo). Úsalo para actuar en contexto.",
    value: ctx,
  });

  // Gate de aprobación humana para las tools de escritura (interrupt de LangGraph).
  useLangGraphInterrupt({
    render: ({ event, resolve }) => {
      const v: any = event.value || {};
      return (
        <div
          style={{
            border: "1px solid #d0d0d0",
            borderRadius: 10,
            padding: 12,
            background: "#fff",
            fontSize: 13,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>
            🔐 Aprobación requerida
          </div>
          <div style={{ marginBottom: 8 }}>{v.message || "El agente propone una acción."}</div>
          {v.tool && (
            <div style={{ color: "#666", marginBottom: 4 }}>
              Acción: <code>{v.tool}</code>
            </div>
          )}
          <pre
            style={{
              background: "#f6f6f6",
              padding: 8,
              borderRadius: 6,
              maxHeight: 180,
              overflow: "auto",
            }}
          >
            {JSON.stringify(v.args, null, 2)}
          </pre>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button
              onClick={() => resolve({ approved: true })}
              style={{
                background: "#2e7d32",
                color: "#fff",
                border: 0,
                borderRadius: 6,
                padding: "6px 12px",
                cursor: "pointer",
              }}
            >
              Aprobar
            </button>
            <button
              onClick={() =>
                resolve({ approved: false, reason: "Rechazado por el usuario" })
              }
              style={{
                background: "#eee",
                border: 0,
                borderRadius: 6,
                padding: "6px 12px",
                cursor: "pointer",
              }}
            >
              Rechazar
            </button>
          </div>
        </div>
      );
    },
  });

  // Remonta el iframe cuando cambia el número de paneles (refleja lo que crea el agente).
  const iframeSrc = `${GRAFANA_URL}/d/${DASH_UID}/copilot-dashboard?kiosk&theme=light&from=now-30y&to=now`;

  return (
    <main style={{ display: "flex", height: "100vh", width: "100vw" }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <iframe
          key={ctx.panels.length}
          src={iframeSrc}
          style={{ width: "100%", height: "100%", border: 0 }}
          title="Grafana"
        />
      </div>
      <CopilotSidebar
        defaultOpen
        clickOutsideToClose={false}
        labels={{
          title: "Grafana Copilot",
          initial:
            "Hola 👋 Soy tu copiloto de Grafana. Puedo analizar tu base de datos y construir paneles. ¿Empezamos?",
        }}
      />
    </main>
  );
}
