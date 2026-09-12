"use client";

import { useMemo } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { HttpAgent } from "@ag-ui/client";

// react-core 1.71 es AG-UI: conectamos un HttpAgent directo al backend Python (/agui),
// sin runtime intermedio (runtimeUrl es opcional). El nombre debe coincidir con el
// agente registrado en el backend: "grafana_copilot".
export function Providers({ children }: { children: React.ReactNode }) {
  const agent = useMemo(
    () =>
      new HttpAgent({
        url: process.env.NEXT_PUBLIC_AGUI_URL || "http://localhost:8000/agui",
      }),
    []
  );

  return (
    <CopilotKit
      agent="grafana_copilot"
      agents__unsafe_dev_only={{ grafana_copilot: agent }}
    >
      {children}
    </CopilotKit>
  );
}
