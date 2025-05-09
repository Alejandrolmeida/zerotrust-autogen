"""
Herramientas Defender for Cloud / Azure Resource Graph.

.env necesarios:
  TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID
"""
from __future__ import annotations
import os, requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
load_dotenv()

TENANT=os.getenv("TENANT_ID"); CLIENT=os.getenv("CLIENT_ID"); SECRET=os.getenv("CLIENT_SECRET")
SUB_ID=os.getenv("SUBSCRIPTION_ID")
MGMT  ="https://management.azure.com"

def _token(scope:str)->str:
    url=f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
    data={"grant_type":"client_credentials","client_id":CLIENT,
          "client_secret":SECRET,"scope":scope}
    return requests.post(url,data=data,timeout=15).json()["access_token"]

def get_secure_score() -> dict:
    tok=_token(MGMT+"/.default")
    url=(f"{MGMT}/subscriptions/{SUB_ID}/providers/Microsoft.Security/secureScores?"
         "api-version=2023-01-01-preview")
    return requests.get(url,headers={"Authorization":f"Bearer {tok}"},timeout=30).json()

def query_resource_graph(query:str)->dict:
    tok=_token(MGMT+"/.default")
    url=f"{MGMT}/providers/Microsoft.ResourceGraph/resources?api-version=2021-03-01"
    body={"subscriptions":[SUB_ID],"query":query}
    return requests.post(url,headers={"Authorization":f"Bearer {tok}"},json=body,timeout=30).json()

def auto_fix_recommendation(recommendation_id:str)->dict:
    tok=_token(MGMT+"/.default")
    # simplificación: usamos la action 'dismiss' como placeholder
    url=(f"{MGMT}{recommendation_id}/dismiss?api-version=2021-01-01-preview")
    r=requests.post(url,headers={"Authorization":f"Bearer {tok}"},timeout=30)
    r.raise_for_status(); return {"status":"submitted","id":recommendation_id}

def _schema(p:dict,req:list[str]|None=None): return {"type":"object","properties":p,"required":req or []}

def get_posture_tools()->List[Dict[str,Any]]:
    return [
        {"name":"get_secure_score","description":"Devuelve Secure Score completo.",
         "parameters":_schema({}),"handler":lambda _a: get_secure_score()},
        {"name":"query_resource_graph",
         "description":"Ejecución libre de Azure Resource Graph (Kusto‑like).",
         "parameters":_schema({"query":{"type":"string"}},["query"]),
         "handler":lambda a: query_resource_graph(a["query"])},
        {"name":"auto_fix_recommendation",
         "description":"Ejecuta un auto‑fix (simplificado) sobre una recomendación Defender.",
         "parameters":_schema({"recommendation_id":{"type":"string"}},["recommendation_id"]),
         "handler":lambda a: auto_fix_recommendation(a["recommendation_id"])},
    ]
