"""
posture_tools.py
────────────────────────────────────────────────────────────────────────
Utilidades de “Posture & Secure Score” para Zero-Trust Autogen
(sin clases, 100 % funciones).

Funciones expuestas
───────────────────
• get_secure_score()                 → dict   - score numérico + %  
• list_posture_recommendations(...)  → list   - recomendaciones (filtro fecha opc.)  
• get_detailed_recommendation(id)    → dict   - detalles + recursos afectados

Requiere en .env (o variables de entorno):

    TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID
────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
import os, re, requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import azure.identity

load_dotenv()

# ──────────────────────────────────────────────────────────────────────
# credenciales & token helpers
# ──────────────────────────────────────────────────────────────────────
def _azure_env() -> tuple[str, str, str, str]:
    tenant  = os.getenv("TENANT_ID")
    client  = os.getenv("CLIENT_ID")
    secret  = os.getenv("CLIENT_SECRET")
    sub_id  = os.getenv("SUBSCRIPTION_ID")
    if not all([tenant, client, secret, sub_id]):
        raise EnvironmentError(
            "Faltan TENANT_ID, CLIENT_ID, CLIENT_SECRET o SUBSCRIPTION_ID en variables de entorno")
    return tenant, client, secret, sub_id


_TOKEN: dict[str, Any] = {"value": None, "exp": None}


def _get_token() -> str:
    """Devuelve un token de AAD con caché de 5 min de margen."""
    if _TOKEN["value"] and _TOKEN["exp"] and datetime.utcnow() < _TOKEN["exp"]:
        return _TOKEN["value"]

    tenant, client, secret, _ = _azure_env()
    cred  = azure.identity.ClientSecretCredential(tenant_id=tenant, client_id=client, client_secret=secret)
    token = cred.get_token("https://management.azure.com/.default")

    _TOKEN["value"] = token.token
    _TOKEN["exp"]   = datetime.utcnow() + timedelta(seconds=token.expires_on - 300)
    return _TOKEN["value"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json"}


# ──────────────────────────────────────────────────────────────────────
# posture helpers
# ──────────────────────────────────────────────────────────────────────
def _parse_date_filter(date_filter: str) -> Optional[datetime]:
    """Convierte 'today', 'last week', 'last 30 days'… a datetime límite."""
    if not date_filter:
        return None
    now = datetime.utcnow()
    df  = date_filter.lower().strip()

    if df == "today":
        return datetime(now.year, now.month, now.day)
    if df == "yesterday":
        return datetime(now.year, now.month, now.day) - timedelta(days=1)
    if df == "this week":
        return now - timedelta(days=now.weekday())
    if df == "last week":
        return now - timedelta(days=7)

    m = re.match(r"last\s+(\d+)\s+days?", df)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.match(r"last\s+(\d+)\s+months?", df)
    if m:
        return now - timedelta(days=30*int(m.group(1)))

    # si no se entiende → None
    return None


# ──────────────────────────────────────────────────────────────────────
# API calls
# ──────────────────────────────────────────────────────────────────────
def get_secure_score() -> Dict[str, Any]:
    """Devuelve Secure Score (current, max, % y lastUpdated)."""
    _, _, _, sub = _azure_env()
    url = (f"https://management.azure.com/subscriptions/{sub}"
           "/providers/Microsoft.Security/secureScores/ascScore"
           "?api-version=2020-01-01")
    rsp = requests.get(url, headers=_headers(), timeout=30)
    rsp.raise_for_status()
    data = rsp.json()

    cur = data.get("properties", {}).get("score", {}).get("current", 0)
    max_ = data.get("properties", {}).get("score", {}).get("max", 100)
    pct = round(cur / max_ * 100, 2) if max_ else 0.0
    return {
        "currentScore": cur,
        "maxScore": max_,
        "percentageScore": pct,
        "lastUpdated": data.get("properties", {}).get("lastUpdatedUtc", "Unknown")
    }


def list_posture_recommendations(date_filter: str | None = None) -> List[Dict[str, Any]]:
    """Lista recomendaciones fallidas, ordenadas por severidad (High→Low)."""
    _, _, _, sub = _azure_env()
    url = (f"https://management.azure.com/subscriptions/{sub}"
           "/providers/Microsoft.Security/assessments"
           "?api-version=2020-01-01")
    rsp = requests.get(url, headers=_headers(), timeout=60)
    rsp.raise_for_status()
    assessments = rsp.json().get("value", [])

    recs: List[Dict[str, Any]] = []
    for ass in assessments:
        stat = ass.get("properties", {}).get("status", {}).get("code", "")
        if stat == "Healthy":
            continue

        meta = ass.get("properties", {}).get("metadata", {})
        recs.append({
            "id":   ass.get("name"),
            "name": ass.get("properties", {}).get("displayName", "Unknown"),
            "category":  meta.get("category", "Unknown"),
            "severity":  meta.get("severity", "Low"),
            "status":    stat,
            "description": meta.get("description", ""),
            "createdAt": ass.get("properties", {}).get("timeGenerated", "")
        })

    # filtro fecha
    if date_filter:
        threshold = _parse_date_filter(date_filter)
        if threshold:
            tmp = []
            for r in recs:
                try:
                    dt = datetime.strptime(r["createdAt"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
                    if dt >= threshold:
                        tmp.append(r)
                except Exception:
                    tmp.append(r)
            recs = tmp

    order = {"High": 0, "Medium": 1, "Low": 2}
    recs.sort(key=lambda x: order.get(x["severity"], 3))
    return recs


def get_detailed_recommendation(recommendation_id: str) -> Dict[str, Any]:
    """Devuelve detalles + recursos afectados para la recomendación dada."""
    _, _, _, sub = _azure_env()
    hdr = _headers()

    ass_url = (f"https://management.azure.com/subscriptions/{sub}"
               f"/providers/Microsoft.Security/assessments/{recommendation_id}"
               "?api-version=2020-01-01")
    ass_rsp = requests.get(ass_url, headers=hdr, timeout=30)
    ass_rsp.raise_for_status()
    ass = ass_rsp.json()

    # sub‑assessments (recursos afectados)
    affected: List[Dict[str, str]] = []
    sub_url = (f"https://management.azure.com/subscriptions/{sub}"
               f"/providers/Microsoft.Security/assessments/{recommendation_id}/subassessments"
               "?api-version=2019-01-01-preview")
    try:
        sub_rsp = requests.get(sub_url, headers=hdr, timeout=30)
        if sub_rsp.status_code == 200:
            for s in sub_rsp.json().get("value", []):
                rid = s.get("properties", {}).get("resourceDetails", {}).get("id", "")
                rtype = "Unknown"
                parts = rid.split("/")
                if len(parts) > 7:
                    rtype = f"{parts[6]}/{parts[7]}"
                affected.append({
                    "resourceId": rid,
                    "resourceType": rtype,
                    "status": s.get("properties", {}).get("status", {}).get("code", "Unknown")
                })
    except Exception:
        pass  # seguimos sin recursos

    meta = ass.get("properties", {}).get("metadata", {})
    return {
        "id":   ass.get("name"),
        "name": ass.get("properties", {}).get("displayName", "Unknown"),
        "category":  meta.get("category", "Unknown"),
        "severity":  meta.get("severity", "Low"),
        "status":    ass.get("properties", {}).get("status", {}).get("code", "Unknown"),
        "description": meta.get("description", ""),
        "remediation": meta.get("remediationDescription", ""),
        "createdAt":   ass.get("properties", {}).get("timeGenerated", ""),
        "affectedResources": affected
    }
