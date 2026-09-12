"""GrafanaPanelToolKit — tools que ACTÚAN sobre un dashboard vivo de Grafana.

Reutilizado de chatGrafana (como librería). Las tools de ESCRITURA
(create/edit/delete) se envolverán en el gate de aprobación humana en la Fase 2.
"""
import json
from typing import Any, Dict, List, Sequence

import requests
from jsonpath_ng import parse
from langchain_core.tools import StructuredTool
from langchain_core.tools.base import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.row import Row


class GrafanaPanelToolKit:
    def __init__(self, grafana_url: str, grafana_token: str, dashboard_uid: str, engine: Engine):
        self.grafana_url = grafana_url.rstrip("/")
        self.dashboard_uid = dashboard_uid
        self.engine = engine
        self.headers = {
            "Authorization": f"Bearer {grafana_token}",
            "Content-Type": "application/json",
        }

    # --- helpers ---

    def _fetch_dashboard_json(self) -> Dict:
        r = requests.get(
            f"{self.grafana_url}/api/dashboards/uid/{self.dashboard_uid}", headers=self.headers
        )
        if not r.ok:
            raise ValueError(f"Error al obtener dashboard: {r.text}")
        return r.json().get("dashboard")

    def _save_dashboard(self, dashboard_json: Dict) -> str:
        r = requests.post(
            f"{self.grafana_url}/api/dashboards/db",
            headers=self.headers,
            data=json.dumps({"dashboard": dashboard_json, "overwrite": True}),
            timeout=30,
        )
        if not r.ok:
            return f"Error al actualizar dashboard: {r.text}"
        return "Dashboard actualizado exitosamente en Grafana."

    # --- read tools ---

    def _get_panels_summary(self) -> str:
        try:
            panels = self._fetch_dashboard_json().get("panels", [])
            out = f"En el dashboard hay {len(panels)} paneles.\nDetalles:\n"
            for p in panels:
                out += f"- ID: {p.get('id','N/A')} | Título: {p.get('title','Sin título')} | Tipo: {p.get('type','?')}\n"
            return out
        except Exception as e:
            return f"Error obteniendo resumen: {e}"

    def _get_json_panel_by_id(self, idx: int) -> Dict | str:
        try:
            for p in self._fetch_dashboard_json().get("panels", []):
                if p.get("id") == idx:
                    return p
            return f"No se encontró ningún panel con id {idx}"
        except Exception as e:
            return f"Error al buscar panel: {e}"

    def _query_data_base(self, query: str) -> Sequence[Row] | str:
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(text(query)).fetchall()
            if not rows:
                return "El resultado de la query es un conjunto vacío"
            return str(rows[:15])
        except Exception as e:
            return f"Error ejecutando query SQL: {e}"

    # --- write tools (irán tras el gate) ---

    def _create_panel(self, new_json_panel: str) -> str:
        try:
            dash = self._fetch_dashboard_json()
            ids = {p.get("id") for p in dash.get("panels", [])}
            panel = json.loads(new_json_panel.replace("```json", "").replace("```", "").strip())
            if "id" not in panel:
                panel["id"] = (max(ids) if ids else 0) + 1
            if panel["id"] in ids:
                return f"Error: el ID {panel['id']} ya existe. IDs usados: {ids}"
            dash.setdefault("panels", []).append(panel)
            return self._save_dashboard(dash)
        except json.JSONDecodeError:
            return "Error: el string proporcionado no es un JSON válido."
        except Exception as e:
            return f"Error creando panel: {e}"

    def _edit_json_panel(self, panel_id: int, path_json_panel: str, nuevo_valor: Any) -> str:
        try:
            dash = self._fetch_dashboard_json()
            panels = dash.get("panels", [])
            idx = next((i for i, p in enumerate(panels) if p.get("id") == panel_id), -1)
            if idx == -1:
                return f"Error: no existe el panel con ID {panel_id}"
            expr = parse(path_json_panel)
            if expr.find(panels[idx]):
                expr.update(panels[idx], nuevo_valor)
            else:
                cur = panels[idx]
                parts = path_json_panel.replace("$.", "").split(".")
                for part in parts[:-1]:
                    cur = cur.setdefault(part, {})
                cur[parts[-1]] = nuevo_valor
            return self._save_dashboard(dash)
        except Exception as e:
            return f"Error editando panel: {e}"

    def _delete_panel(self, panel_id: int) -> str:
        try:
            dash = self._fetch_dashboard_json()
            before = len(dash.get("panels", []))
            dash["panels"] = [p for p in dash.get("panels", []) if p.get("id") != panel_id]
            if len(dash["panels"]) == before:
                return f"No se encontró panel con ID {panel_id} para eliminar."
            return self._save_dashboard(dash)
        except Exception as e:
            return f"Error eliminando panel: {e}"

    # --- args ---

    class PanelIdArgs(BaseModel):
        idx: int = Field(description="ID numérico del panel.")

    class QueryArgs(BaseModel):
        query: str = Field(description="Query SQL válida para PostgreSQL.")

    class EditArgs(BaseModel):
        panel_id: int = Field(description="ID del panel a modificar.")
        path_json_panel: str = Field(description="JSONPath del campo (ej: '$.title' o '$.targets[0].rawSql').")
        nuevo_valor: Any = Field(description="Nuevo valor a asignar.")

    class CreateArgs(BaseModel):
        new_json_panel: str = Field(description="String con el JSON completo del nuevo panel.")

    class DeleteArgs(BaseModel):
        panel_id: int = Field(description="ID del panel a eliminar.")

    # --- tools ---

    def read_tools(self) -> List[BaseTool]:
        return [
            StructuredTool.from_function(
                name="get_panels_summary",
                description="Lista ID, título y tipo de todos los paneles del dashboard.",
                func=self._get_panels_summary,
            ),
            StructuredTool.from_function(
                name="get_json_panel_by_id",
                description="Retorna el JSON de configuración de un panel dado su ID.",
                func=self._get_json_panel_by_id,
                args_schema=self.PanelIdArgs,
            ),
        ]

    def write_tools(self) -> List[BaseTool]:
        """ESCRITURA — envolver en el gate de aprobación (Fase 2)."""
        return [
            StructuredTool.from_function(
                name="create_panel",
                description="Agrega un nuevo panel al dashboard desde un string JSON válido.",
                func=self._create_panel,
                args_schema=self.CreateArgs,
            ),
            StructuredTool.from_function(
                name="edit_json_panel",
                description="Modifica un campo de un panel usando JSONPath (título, rawSql, tipo, etc.).",
                func=self._edit_json_panel,
                args_schema=self.EditArgs,
            ),
            StructuredTool.from_function(
                name="delete_panel",
                description="Elimina permanentemente un panel del dashboard dado su ID.",
                func=self._delete_panel,
                args_schema=self.DeleteArgs,
            ),
        ]
