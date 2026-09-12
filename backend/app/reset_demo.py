"""Resetea el dashboard de demo (copilot-main) a un estado limpio para grabar.

Uso:
  cd backend && ./.venv/bin/python -m app.reset_demo          # deja el dashboard vacío
  cd backend && ./.venv/bin/python -m app.reset_demo --keep   # conserva paneles
"""
import json
import sys

import requests

from app.grafana_bootstrap import COPILOT_DASHBOARD_UID
from app.settings import settings


def reset(empty: bool = True) -> None:
    auth = (settings.grafana_admin_user, settings.grafana_admin_password)
    base = settings.grafana_url
    r = requests.get(f"{base}/api/dashboards/uid/{COPILOT_DASHBOARD_UID}", auth=auth)
    dash = r.json()["dashboard"] if r.ok else {
        "uid": COPILOT_DASHBOARD_UID,
        "title": "Copilot Dashboard",
        "schemaVersion": 39,
    }
    if empty:
        dash["panels"] = []
    dash.setdefault("time", {"from": "now-30y", "to": "now"})
    resp = requests.post(
        f"{base}/api/dashboards/db",
        auth=auth,
        json={"dashboard": dash, "overwrite": True},
    )
    print("reset:", resp.json().get("status"), "| paneles:", len(dash.get("panels", [])))


if __name__ == "__main__":
    reset(empty="--keep" not in sys.argv)
