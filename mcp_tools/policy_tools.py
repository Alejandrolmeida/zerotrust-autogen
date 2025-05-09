"""
Tools para crear / validar / asignar Azure Policy JSON.

.env: TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID
"""
from __future__ import annotations
import os, requests, datetime, json
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

TENANT=os.getenv("TENANT_ID"); CLIENT=os.getenv("CLIENT_ID"); SECRET=os.getenv("CLIENT_SECRET")
SUB_ID=os.getenv("SUBSCRIPTION_ID"); MGMT="https://management.azure.com"

def _token()->str:
    url=f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
    data={"grant_type":"client_credentials","client_id":CLIENT,"client_secret":SECRET,
          "scope":MGMT+"/.default"}
    return requests.post(url,data=data,timeout=15).json()["access_token"]

HDR=lambda:{"Authorization":f"Bearer {_token()}","Content-Type":"application/json"}

def assign_policy(policy_json:dict, scope:str, name:str|None=None)->dict:
    name = name or f"autoPolicy-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    url  = f"{MGMT}{scope}/providers/Microsoft.Authorization/policyAssignments/{name}?api-version=2022-06-01"
    body = {"properties":{"displayName":name,"policyDefinition":policy_json}}
    r=requests.put(url,headers=HDR(),json=body,timeout=30); r.raise_for_status(); return r.json()

def validate_policy(policy_json:dict)->dict:
    # Placeholder: en real usarías la API de policyInsights/explain
    return {"valid": True, "rules": len(policy_json.get("policyRule",{}).get("if",{}))}

def _schema(p:dict,req:list[str]|None=None): return {"type":"object","properties":p,"required":req or []}

def get_policy_tools()->List[Dict[str,Any]]:
    return [
        {"name":"validate_policy_json",
         "description":"Valida sintaxis básica de un Azure Policy JSON.",
         "parameters":_schema({"policy":{"type":"object"}},["policy"]),
         "handler":lambda a: validate_policy(a["policy"])},
        {"name":"assign_policy",
         "description":"Asigna (o reemplaza) un Azure Policy en el scope indicado.",
         "parameters":_schema({
             "policy":{"type":"object"},
             "scope":{"type":"string",
                      "description":"Ej. /subscriptions/xxx/resourceGroups/rg‑prod"},
             "name":{"type":"string"}
         },["policy","scope"]),
         "handler":lambda a: assign_policy(a["policy"],a["scope"],a.get("name"))},
    ]
