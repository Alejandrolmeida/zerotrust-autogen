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
    """
    Lista las definiciones de políticas disponibles en la suscripción.

    Args:
        subscription_id: ID de la suscripción (opcional).

    Returns:
        Lista de definiciones de políticas.
    """
    try:
        if not subscription_id:
            _, _, _, subscription_id = _azure_env()
        headers = _headers()
        url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Authorization/policyDefinitions?api-version=2021-06-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])
    except requests.RequestException as e:
        print(f"Error al listar definiciones de políticas: {e}")
        return []

def get_policy_definition(policy_name: str) -> Dict[str, Any]:
    """
    Recupera una definición de política por nombre o ID.

    Args:
        policy_name: Nombre o ID de la política.

    Returns:
        Definición de la política.
    """
    try:
        headers = _headers()
        url = f"https://management.azure.com/providers/Microsoft.Authorization/policyDefinitions/{policy_name}?api-version=2021-06-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al obtener la definición de la política: {e}")
        return {}

def assign_policy(policy_name: str, scope: str) -> Dict[str, Any]:
    """
    Asigna una política a un scope específico.

    Args:
        policy_name: Nombre o ID de la política.
        scope: Scope al que se asignará la política.

    Returns:
        Resultado de la asignación.
    """
    try:
        headers = _headers()
        url = f"https://management.azure.com/{scope}/providers/Microsoft.Authorization/policyAssignments/{policy_name}?api-version=2021-06-01"
        payload = {
            "properties": {
                "policyDefinitionId": f"/providers/Microsoft.Authorization/policyDefinitions/{policy_name}"
            }
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al asignar la política: {e}")
        return {}

def list_policy_assignments(subscription_id: str | None = None) -> List[Dict[str, Any]]:
    """
    Lista las asignaciones de políticas en la suscripción.

    Args:
        subscription_id: ID de la suscripción (opcional).

    Returns:
        Lista de asignaciones de políticas.
    """
    try:
        if not subscription_id:
            _, _, _, subscription_id = _azure_env()
        headers = _headers()
        url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Authorization/policyAssignments?api-version=2021-06-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])
    except requests.RequestException as e:
        print(f"Error al listar asignaciones de políticas: {e}")
        return []

def save_report(report_name: str, content: str):
    """
    Guarda el contenido del informe en la carpeta `report`.

    Args:
        report_name: Nombre del archivo del informe.
        content: Contenido del informe.
    """
    report_dir = os.path.join(os.getcwd(), "report")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, report_name)
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(content)
    return report_path

def generate_policy_report(definitions: list, assignments: list) -> str:
    """
    Genera un informe detallado de las políticas y asignaciones.

    Args:
        definitions: Lista de definiciones de políticas.
        assignments: Lista de asignaciones de políticas.

    Returns:
        Nombre del archivo del informe generado.
    """
    report_content = """# Informe de Políticas de Azure\n\n## Definiciones de Políticas\n"""
    for definition in definitions:
        report_content += f"- {definition.get('displayName', 'Sin nombre')}\n"

    report_content += "\n## Asignaciones de Políticas\n"
    for assignment in assignments:
        report_content += f"- {assignment.get('name', 'Sin nombre')}\n"

    report_name = "policy_report.md"
    save_report(report_name, report_content)
    return report_name

