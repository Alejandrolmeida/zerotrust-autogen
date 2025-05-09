"""
Tools GitHub REST v3 para:
  • create_branch_from_default
  • commit_files_to_branch
  • create_pull_request
  • trigger_workflow_run  (GitHub Actions workflow_dispatch)

Requiere en .env
  GITHUB_PAT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  GITHUB_OWNER=my‑org‑or‑user
"""
from __future__ import annotations
import os, base64, requests, json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
load_dotenv()

API   = "https://api.github.com"
OWNER = os.getenv("GITHUB_OWNER")
TOKEN = os.getenv("GITHUB_PAT")
if not (OWNER and TOKEN):
    raise ValueError("Faltan GITHUB_OWNER o GITHUB_PAT en .env")

def _hdr() -> dict:
    return {"Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json"}

# ──────────────────────────────────────────────
#  operaciones
# ──────────────────────────────────────────────
def _default_branch(repo:str)->str:
    return requests.get(f"{API}/repos/{OWNER}/{repo}",
                        headers=_hdr(),timeout=15).json()["default_branch"]

def create_branch_from_default(repo:str, new_branch:str)->dict:
    default = _default_branch(repo)
    sha = requests.get(f"{API}/repos/{OWNER}/{repo}/git/ref/heads/{default}",
                       headers=_hdr(),timeout=15).json()["object"]["sha"]
    body = {"ref": f"refs/heads/{new_branch}", "sha": sha}
    r = requests.post(f"{API}/repos/{OWNER}/{repo}/git/refs",
                      headers=_hdr(),json=body,timeout=15)
    r.raise_for_status(); return r.json()

def commit_files_to_branch(repo:str, branch:str,
                           files:dict[str,str], commit_msg:str)->dict:
    # files = { path : raw‑content }
    # 1) obtener último tree sha
    head = requests.get(f"{API}/repos/{OWNER}/{repo}/git/ref/heads/{branch}",
                        headers=_hdr(),timeout=15).json()
    base_tree = head["object"]["sha"]
    # 2) crear blobs
    blobs=[]
    for path,content in files.items():
        b = requests.post(f"{API}/repos/{OWNER}/{repo}/git/blobs",
                          headers=_hdr(),
                          json={"content":content,"encoding":"utf-8"},timeout=15).json()
        blobs.append({"path":path,"mode":"100644","type":"blob","sha":b["sha"]})
    # 3) crear nuevo tree
    tree = requests.post(f"{API}/repos/{OWNER}/{repo}/git/trees",
                         headers=_hdr(),
                         json={"base_tree":base_tree,"tree":blobs},timeout=15).json()
    # 4) crear commit
    commit = requests.post(f"{API}/repos/{OWNER}/{repo}/git/commits",
                           headers=_hdr(),
                           json={"message":commit_msg,"tree":tree["sha"],
                                 "parents":[base_tree]},timeout=15).json()
    # 5) mover la ref
    requests.patch(f"{API}/repos/{OWNER}/{repo}/git/refs/heads/{branch}",
                   headers=_hdr(),json={"sha":commit["sha"]},timeout=15).raise_for_status()
    return commit

def create_pull_request(repo:str, head:str, base:str,
                        title:str, body:str|None=None)->dict:
    payload={"title":title,"head":head,"base":base,"body":body or ""}
    r=requests.post(f"{API}/repos/{OWNER}/{repo}/pulls",
                    headers=_hdr(),json=payload,timeout=15)
    r.raise_for_status(); return r.json()

def trigger_workflow_run(repo:str, workflow:str, ref:str,
                         inputs:Optional[dict]=None)->dict:
    # workflow: nombre.yml  ó  id numérico
    url=f"{API}/repos/{OWNER}/{repo}/actions/workflows/{workflow}/dispatches"
    r=requests.post(url,headers=_hdr(),json={"ref":ref,"inputs":inputs or {}},timeout=15)
    r.raise_for_status(); return {"status":"queued","workflow":workflow,"ref":ref}

# ──────────────────────────────────────────────
#  export para MCP/autogen
# ──────────────────────────────────────────────
def _schema(props:dict, req:list[str]|None=None)->dict:
    return {"type":"object","properties":props,"required":req or []}

def get_github_tools()->List[Dict[str,Any]]:
    return [
        {
            "name":"create_branch",
            "description":"Crea una rama desde el branch por defecto.",
            "parameters":_schema({
                "repo":{"type":"string"},
                "new_branch":{"type":"string"}
            },["repo","new_branch"]),
            "handler":lambda a: create_branch_from_default(a["repo"],a["new_branch"])
        },
        {
            "name":"commit_files",
            "description":"Añade / actualiza ficheros en una rama.",
            "parameters":_schema({
                "repo":{"type":"string"},
                "branch":{"type":"string"},
                "files":{"type":"object",
                         "description":"objeto { ruta : contenido‑texto }"},
                "message":{"type":"string"}
            },["repo","branch","files","message"]),
            "handler":lambda a: commit_files_to_branch(
                a["repo"],a["branch"],a["files"],a["message"])
        },
        {
            "name":"create_pull_request",
            "description":"Abre un PR entre dos ramas.",
            "parameters":_schema({
                "repo":{"type":"string"},
                "head":{"type":"string","description":"rama origen"},
                "base":{"type":"string","description":"rama destino"},
                "title":{"type":"string"},
                "body":{"type":"string"}
            },["repo","head","base","title"]),
            "handler":lambda a: create_pull_request(
                a["repo"],a["head"],a["base"],a["title"],a.get("body"))
        },
        {
            "name":"trigger_workflow",
            "description":"Lanza manualmente un workflow_dispatch.",
            "parameters":_schema({
                "repo":{"type":"string"},
                "workflow":{"type":"string","description":"id o *.yml"},
                "ref":{"type":"string","description":"branch o tag"},
                "inputs":{"type":"object"}
            },["repo","workflow","ref"]),
            "handler":lambda a: trigger_workflow_run(
                a["repo"],a["workflow"],a["ref"],a.get("inputs"))
        },
    ]
