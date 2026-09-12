import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  EmptyAdapter,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

// El runtime de CopilotKit reenvía las llamadas al agente Python (FastAPI /copilotkit).
// EmptyAdapter: el LLM vive en el agente LangGraph, no aquí.
const runtime = new CopilotRuntime({
  remoteEndpoints: [
    { url: process.env.PYTHON_AGENT_URL || "http://localhost:8000/copilotkit" },
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new EmptyAdapter(),
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
