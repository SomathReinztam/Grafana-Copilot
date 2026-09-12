"use client";

import { CopilotKit } from "@copilotkit/react-core";

export function Providers({ children }: { children: React.ReactNode }) {
  // agent debe coincidir con el nombre registrado en el SDK Python: "grafana_copilot"
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="grafana_copilot">
      {children}
    </CopilotKit>
  );
}
