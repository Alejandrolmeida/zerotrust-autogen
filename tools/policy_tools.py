"""
policy_tools.py
────────────────────────────────────────────────────────────────────────
Utilidades de Azure Policy para Zero‑Trust Autogen (estilo *funcional*).

• get_policy_definition()   – recupera una definición por nombre/ID
• list_policy_definitions() – máx 100 (built‑in + custom)
• assign_policy()           – asigna la política a un scope dado
• list_policy_assignments() – muestra asignaciones en la suscripción

Requiere en .env (o variables de entorno a runtime):

    TENANT_ID            AAD tenant
    CLIENT_ID            App registration
    CLIENT_SECRET        Secreto de la app
    SUBSCRIPTION_ID      Suscripción donde operaremos
────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
import os, time, requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import azure.identity

load_dotenv()

# ──────────────────────────────────────────────────────────────────────
# credenciales & token helpers
# ──────────────────────────────────────────────────────────────────────
def _azure_env() -> tuple[str, str, str, str]:
    """Devuelve (tenant_id, client_id, client_secret, subscription_id) o lanza error."""
    tenant  = os.getenv("TENANT_ID")
    client  = os.getenv("CLIENT_ID")
    secret  = os.getenv("CLIENT_SECRET")
    sub_id  = os.getenv("SUBSCRIPTION_ID")
    if not all([tenant, client, secret, sub_id]):
        raise EnvironmentError(
            "Faltan TENANT_ID, CLIENT_ID, CLIENT_SECRET o SUBSCRIPTION_ID en variables de entorno")
    return tenant, client, secret, sub_id


# cache sencillo en módulo
_TOKEN_CACHE: dict[str, Any] = {"token": None, "expires": None}


def _get_token() -> str:
    """Devuelve token válido, renovándolo 5 min antes de caducar."""
    if _TOKEN_CACHE["token"] and _TOKEN_CACHE["expires"] and datetime.utcnow() < _TOKEN_CACHE["expires"]:
        return _TOKEN_CACHE["token"]

    tenant, client, secret, _ = _azure_env()
    cred = azure.identity.ClientSecretCredential(tenant_id=tenant, client_id=client, client_secret=secret)
    token = cred.get_token("https://management.azure.com/.default")

    _TOKEN_CACHE["token"]   = token.token
    _TOKEN_CACHE["expires"] = datetime.utcnow() + timedelta(seconds=token.expires_on - 300)  # 5 min margen
    return _TOKEN_CACHE["token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json"}


# ──────────────────────────────────────────────────────────────────────
# funciones públicas
# ──────────────────────────────────────────────────────────────────────
def list_policy_definitions(subscription_id: str | None = None) -> List[Dict[str, Any]]:
    """Devuelve hasta 100 definiciones (built‑in + custom) de la suscripción."""
    _, _, _, sub = _azure_env()
    sub = subscription_id or sub
    hdr = _headers()

    # built‑in
    builtin = requests.get(
        "https://management.azure.com/providers/Microsoft.Authorization/policyDefinitions"
        "?api-version=2021-06-01", headers=hdr, timeout=30).json().get("value", [])

    # custom (a nivel de subs)
    custom = requests.get(
        f"https://management.azure.com/subscriptions/{sub}/providers/Microsoft.Authorization/policyDefinitions"
        "?api-version=2021-06-01", headers=hdr, timeout=30).json().get("value", [])

    return (builtin + custom)[:100]


def get_policy_definition(policy_name: str) -> Dict[str, Any]:
    """Busca por nombre (o displayName) y devuelve la definición completa."""
    hdr = _headers()
    for pol in list_policy_definitions():
        if policy_name.lower() in pol.get("name", "").lower() or \
           policy_name.lower() in pol.get("properties", {}).get("displayName", "").lower():
            pol_id = pol["id"]
            rsp = requests.get(f"https://management.azure.com{pol_id}?api-version=2021-06-01",
                               headers=hdr, timeout=30)
            rsp.raise_for_status()
            return rsp.json()
    raise ValueError(f"No se encontró definición que coincida con '{policy_name}'")


def assign_policy(policy_name: str, scope: str) -> Dict[str, Any]:
    """Crea una asignación de la política indicada al `scope` (subs, RG…)."""
    hdr           = _headers()
    pol_def       = get_policy_definition(policy_name)
    pol_def_id    = pol_def["id"]
    display_name  = pol_def["properties"].get("displayName", policy_name)
    assignment_id = f"assignment-{int(time.time())}"

    url  = (f"https://management.azure.com{scope}"
            f"/providers/Microsoft.Authorization/policyAssignments/{assignment_id}"
            "?api-version=2021-06-01")

    body = {"properties": {
                "displayName": f"Asignación de {display_name}",
                "policyDefinitionId": pol_def_id,
                "scope": scope
           }}

    rsp = requests.put(url, headers=hdr, json=body, timeout=30)
    rsp.raise_for_status()
    return rsp.json()


def list_policy_assignments(subscription_id: str | None = None) -> List[Dict[str, Any]]:
    """Lista asignaciones de política en la suscripción dada."""
    _, _, _, sub = _azure_env()
    sub = subscription_id or sub
    hdr = _headers()

    url = (f"https://management.azure.com/subscriptions/{sub}"
           "/providers/Microsoft.Authorization/policyAssignments"
           "?api-version=2021-06-01")
    rsp = requests.get(url, headers=hdr, timeout=30)
    rsp.raise_for_status()
    return rsp.json().get("value", [])

