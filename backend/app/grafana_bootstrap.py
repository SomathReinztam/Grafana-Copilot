"""Bootstrap de Grafana: obtiene un token de service account y garantiza que exista
un dashboard sobre el cual el agente pueda actuar."""
import json

import requests

from app.lib.grafana_helper import GrafanaHelper
from app.settings import settings

COPILOT_DASHBOARD_UID = "copilot-main"


def ensure_dashboard(
    base_url: str, token: str, uid: str = COPILOT_DASHBOARD_UID, title: str = "Copilot Dashboard"
) -> str:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.get(f"{base_url}/api/dashboards/uid/{uid}", headers=headers)
    if r.ok:
        return uid
    dashboard = {
        "uid": uid,
        "title": title,
        "tags": ["copilot"],
        "timezone": "browser",
        "schemaVersion": 39,
        # Rango amplio por defecto para que se vean datos históricos (northwind es de los 90s).
        "time": {"from": "now-30y", "to": "now"},
        "panels": [],
    }
    r = requests.post(
        f"{base_url}/api/dashboards/db",
        headers=headers,
        data=json.dumps({"dashboard": dashboard, "overwrite": True}),
        timeout=30,
    )
    r.raise_for_status()
    return uid


def get_datasource(base_url: str, token: str) -> tuple[str | None, str | None]:
    """Devuelve (uid, type) del datasource Postgres (default o el primero)."""
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{base_url}/api/datasources", headers=headers)
    if not r.ok:
        return None, None
    dss = r.json()
    ds = (
        next((d for d in dss if d.get("isDefault")), None)
        or next((d for d in dss if "postgres" in (d.get("type") or "")), None)
        or (dss[0] if dss else None)
    )
    return (ds.get("uid"), ds.get("type")) if ds else (None, None)


def bootstrap_grafana() -> tuple[str, str, str, str | None, str | None]:
    """Devuelve (grafana_url, token, dashboard_uid, datasource_uid, datasource_type)."""
    helper = GrafanaHelper(
        settings.grafana_url, settings.grafana_admin_user, settings.grafana_admin_password
    )
    token = helper.ensure_token()
    uid = ensure_dashboard(settings.grafana_url, token)
    ds_uid, ds_type = get_datasource(settings.grafana_url, token)
    return settings.grafana_url, token, uid, ds_uid, ds_type
