"""Vision: el agente puede VER los paneles renderizados (diagnóstico visual).

- Tool `look_at_panel(panel_id)`: renderiza el panel a PNG y lo inyecta como imagen
  en la conversación (HumanMessage) para que el modelo multimodal (Gemini) lo vea.
- `image_buffer_hook`: mantiene ≤5 imágenes activas. En vez de mutar el historial
  (rompería el pareo tool_call/tool_result), transforma SOLO lo que ve el LLM
  (llm_input_messages), reemplazando las imágenes viejas por un stub de texto.
  Así el modelo mira estratégicamente y no se sobrecarga el contexto.
"""
from typing import Annotated

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command
from pydantic import BaseModel, Field

MAX_ACTIVE_IMAGES = 5
_PANEL_IMAGE_KEY = "panel_image"


def build_look_at_panel_tool(panel_kit):
    class LookArgs(BaseModel):
        panel_id: int = Field(description="ID del panel a mirar (ver get_panels_summary).")

    @tool(args_schema=LookArgs)
    def look_at_panel(panel_id: int, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
        """Renderiza un panel del dashboard y te permite VERLO para diagnosticar visualmente
        (tendencias, huecos, ejes, colores). Máximo 5 imágenes activas: sé estratégico sobre
        qué paneles miras."""
        b64, err = panel_kit.render_panel_png(panel_id)
        if err:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"No pude renderizar el panel {panel_id}: {err}",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )
        image_block = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        }
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Imagen del panel {panel_id} cargada; obsérvala en el siguiente mensaje.",
                        tool_call_id=tool_call_id,
                    ),
                    HumanMessage(
                        content=[
                            {"type": "text", "text": f"[Render del panel {panel_id}]"},
                            image_block,
                        ],
                        additional_kwargs={_PANEL_IMAGE_KEY: panel_id},
                    ),
                ]
            }
        )

    return look_at_panel


def image_buffer_hook(state: dict) -> dict:
    """pre_model_hook: cap de imágenes de panel a MAX_ACTIVE_IMAGES para el LLM,
    sin mutar el state (usa llm_input_messages)."""
    messages = state["messages"]
    img_idxs = [
        i
        for i, m in enumerate(messages)
        if isinstance(m, HumanMessage)
        and isinstance(getattr(m, "additional_kwargs", None), dict)
        and m.additional_kwargs.get(_PANEL_IMAGE_KEY) is not None
    ]
    keep = set(img_idxs[-MAX_ACTIVE_IMAGES:])
    if len(img_idxs) <= MAX_ACTIVE_IMAGES:
        return {"llm_input_messages": messages}

    out = []
    for i, m in enumerate(messages):
        if i in img_idxs and i not in keep:
            pid = m.additional_kwargs.get(_PANEL_IMAGE_KEY)
            out.append(HumanMessage(content=f"[imagen del panel {pid} desalojada del contexto]"))
        else:
            out.append(m)
    return {"llm_input_messages": out}
