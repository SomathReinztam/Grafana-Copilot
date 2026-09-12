"""GrafanaHelper — cliente REST de Grafana (setup: service account, token, datasource,
publicar dashboard). Reutilizado de los repos de referencia y limpiado: config por
constructor, sin secretos hardcodeados, sin print de tokens.
"""
import copy
import json
import uuid
from typing import Dict, Optional

import requests
from requests.auth import HTTPBasicAuth


class GrafanaHelper:
    def __init__(self, base_url: str, admin_user: str, admin_password: str):
        self.base_url = base_url.rstrip("/")
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.service_account_id: Optional[int] = None
        self.token: Optional[str] = None

    @property
    def _auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.admin_user, self.admin_password)

    def _bearer(self) -> Dict[str, str]:
        if not self.token:
            raise ValueError("Token no configurado. Llama a ensure_token() primero.")
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    # Paso 1: service account "Admin"
    def make_service_account(self, name: str = "Admin", role: str = "Admin") -> int:
        r = requests.get(f"{self.base_url}/api/serviceaccounts/search?query={name}", auth=self._auth)
        data = r.json() if r.ok else {}
        accounts = data.get("serviceAccounts", []) if isinstance(data, dict) else data
        for acc in accounts or []:
            if isinstance(acc, dict) and acc.get("name") == name:
                self.service_account_id = acc["id"]
                return self.service_account_id

        r = requests.post(
            f"{self.base_url}/api/serviceaccounts", json={"name": name, "role": role}, auth=self._auth
        )
        r.raise_for_status()
        self.service_account_id = r.json()["id"]
        return self.service_account_id

    # Paso 2: token (rota el anterior si existe)
    def get_token_account(self, name: str = "Admin") -> str:
        if self.service_account_id is None:
            raise ValueError("Llama a make_service_account() primero.")
        existing = requests.get(
            f"{self.base_url}/api/serviceaccounts/{self.service_account_id}/tokens", auth=self._auth
        ).json()
        for tok in existing or []:
            if tok.get("name") == name:
                requests.delete(
                    f"{self.base_url}/api/serviceaccounts/{self.service_account_id}/tokens/{tok['id']}",
                    auth=self._auth,
                )
        r = requests.post(
            f"{self.base_url}/api/serviceaccounts/{self.service_account_id}/tokens",
            json={"name": name},
            auth=self._auth,
        )
        r.raise_for_status()
        self.token = r.json()["key"]
        return self.token

    def ensure_token(self) -> str:
        """Atajo: service account + token en un paso."""
        self.make_service_account()
        return self.get_token_account()

    # Paso 3: registrar datasource Postgres -> devuelve UID
    def get_db_grafana_uid(
        self, db_user: str, db_password: str, db_host: str, db_name: str, db_port: str = "5432"
    ) -> str:
        headers = self._bearer()
        url = f"{self.base_url}/api/datasources"
        name = f"Postgres-{db_name}-{db_host}-{db_port}"
        datasources = requests.get(url, headers=headers).json()
        existing = next((d for d in datasources if d.get("name") == name), None)
        if existing:
            return existing.get("uid")
        has_default = any(d.get("isDefault") for d in datasources)

        payload = {
            "name": name,
            "type": "grafana-postgresql-datasource",
            "access": "proxy",
            "url": f"{db_host}:{db_port}",
            "user": db_user,
            "database": db_name,
            "basicAuth": False,
            "isDefault": not has_default,
            "jsonData": {"sslmode": "disable", "database": db_name, "postgresVersion": 1500},
            "secureJsonData": {"password": db_password},
        }
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code >= 300:
            raise Exception(f"Error creando datasource: {r.text}")
        return r.json()["datasource"]["uid"]

    # Publicar un dashboard completo
    def push_grafana_dashboard(self, grafana_json: Dict, overwrite: bool = False) -> Dict:
        dashboard = copy.deepcopy(grafana_json)
        dashboard["uid"] = dashboard.get("uid") or str(uuid.uuid4())
        dashboard["version"] = 1
        for i, panel in enumerate(dashboard.get("panels", []), start=1):
            panel["id"] = i
        r = requests.post(
            f"{self.base_url}/api/dashboards/db",
            headers=self._bearer(),
            data=json.dumps({"dashboard": dashboard, "overwrite": overwrite}),
            timeout=30,
        )
        if r.json().get("status") != "success":
            raise ValueError(f"Error publicando dashboard ({r.status_code}): {r.text}")
        return r.json()
