"""Gate de aprobación humana para tools de escritura, vía interrupt() de LangGraph.

Cuando el agente invoca una tool envuelta, el grafo se PAUSA (interrupt) y expone la
propuesta al cliente. El cliente reanuda con Command(resume={"approved": bool, ...}).
En el frontend esto se renderiza con el hook useLangGraphInterrupt de CopilotKit.
"""
from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.types import interrupt


def gated_tool(tool: StructuredTool) -> StructuredTool:
    original_func = tool.func

    def _wrapped(**kwargs: Any) -> str:
        decision = interrupt(
            {
                "kind": "approval_request",
                "tool": tool.name,
                "args": kwargs,
                "message": f"El agente propone ejecutar '{tool.name}'. ¿Apruebas?",
            }
        )
        if isinstance(decision, dict):
            approved = decision.get("approved", False)
            args = decision.get("args") or kwargs  # el usuario puede editar los args
            reason = decision.get("reason")
        else:
            approved = bool(decision)
            args, reason = kwargs, None

        if not approved:
            return f"El usuario RECHAZÓ la acción '{tool.name}'." + (
                f" Motivo: {reason}" if reason else ""
            )
        return original_func(**args)

    return StructuredTool.from_function(
        name=tool.name,
        description=tool.description,
        func=_wrapped,
        args_schema=tool.args_schema,
    )
