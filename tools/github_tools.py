"""
github_tools.py
────────────────────────────────────────────────────────────────────────
Utilidades de GitHub para Zero‑Trust Autogen en estilo *funcional*:

• create_branch()           – crea rama a partir de la default
• list_repositories()       – lista repos del owner/org (+filtro fecha)
• get_repository()          – info detallada de un repo
• get_file_content()        – lee archivo o lista directorio
• create_pull_request()     – abre un PR entre ramas
• list_pull_requests()      – lista PRs (open/closed/all)

Requiere en .env (o variables de entorno a runtime):
    GITHUB_OWNER            owner u organización
    GITHUB_PAT / GITHUB_TOKEN   PAT con scope repo
────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
import os, re, base64, requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────
# helpers internos
# ──────────────────────────────────────────────────────────────────────
def _github_env() -> tuple[str, str, str]:
    """Devuelve (API, owner, token) asegurándose de que existan."""
    api    = "https://api.github.com"
    owner  = os.getenv("GITHUB_OWNER")
    token  = os.getenv("GITHUB_PAT") or os.getenv("GITHUB_TOKEN")
    if not owner or not token:
        raise EnvironmentError(
            "Faltan GITHUB_OWNER y/o GITHUB_PAT|GITHUB_TOKEN en variables de entorno")
    return api, owner, token


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _default_branch_info(repo: str, owner: str, api: str, hdr: dict) -> Dict[str, Any]:
    """Obtiene información (nombre+SHA) de la rama por defecto."""
    repo_info = requests.get(f"{api}/repos/{owner}/{repo}", headers=hdr, timeout=15)
    repo_info.raise_for_status()
    default_branch = repo_info.json()["default_branch"]
    branch = requests.get(f"{api}/repos/{owner}/{repo}/branches/{default_branch}",
                          headers=hdr, timeout=15)
    branch.raise_for_status()
    return branch.json()                       # → { name, commit:{ sha,… } }


def _parse_date_filter(date_filter: str) -> Optional[datetime]:
    """Traduce filtros tipo 'today', 'last 7 days', … a datetime."""
    now = datetime.utcnow()

    df = date_filter.lower().strip()
    if df == "today":
        return datetime(now.year, now.month, now.day)
    if df == "yesterday":
        return datetime(*(now - timedelta(days=1)).timetuple()[:3])
    if df == "this week":
        return now - timedelta(days=now.weekday())
    if df == "last week":
        return now - timedelta(days=7)

    if (m := re.match(r"last\s+(\d+)\s+days?", df)):
        return now - timedelta(days=int(m.group(1)))
    if (m := re.match(r"last\s+(\d+)\s+months?", df)):
        return now - timedelta(days=30 * int(m.group(1)))
    if m:
        return now - timedelta(days=30 * int(m.group(1)))
        return now - timedelta(days=30 * int(m.group(1)))
    return None


# ──────────────────────────────────────────────────────────────────────
# herramientas exportadas
# ──────────────────────────────────────────────────────────────────────
def create_branch(repo: str, new_branch: str, owner: str | None = None) -> Dict[str, Any]:
    """Crea una nueva rama a partir de la default branch."""
    api, env_owner, token = _github_env()
    owner = owner or env_owner
    hdr   = _headers(token)

    info  = _default_branch_info(repo, owner, api, hdr)
    sha   = info["commit"]["sha"]

    rsp = requests.post(f"{api}/repos/{owner}/{repo}/git/refs",
                        headers=hdr,
                        json={"ref": f"refs/heads/{new_branch}", "sha": sha},
                        timeout=15)
    rsp.raise_for_status()
    return rsp.json()


def list_repositories(owner: str | None = None,
                      date_filter: str | None = None) -> List[Dict[str, Any]]:
    """Lista repos del owner/org.  `date_filter` como 'last 30 days', etc."""
    api, env_owner, token = _github_env()
    owner = owner or env_owner
    hdr   = _headers(token)

    # ¿org o user?
    who = requests.get(f"{api}/users/{owner}", headers=hdr, timeout=15).json()["type"]
    repos_url = f"{api}/orgs/{owner}/repos?per_page=100" if who == "Organization" \
               else f"{api}/users/{owner}/repos?per_page=100"
    repos = requests.get(repos_url, headers=hdr, timeout=15)
    repos.raise_for_status()
    lst = repos.json()

    if date_filter:
        th = _parse_date_filter(date_filter)
        if th:
            lst = [r for r in lst
                   if datetime.strptime(r["updated_at"], "%Y-%m-%dT%H:%M:%SZ") >= th]
    return lst


def get_repository(repo: str, owner: str | None = None) -> Dict[str, Any]:
    """Detalles de un repo."""
    api, env_owner, token = _github_env()
    owner = owner or env_owner
    hdr   = _headers(token)

    rsp = requests.get(f"{api}/repos/{owner}/{repo}", headers=hdr, timeout=15)
    rsp.raise_for_status()
    return rsp.json()


def get_file_content(repo: str, path: str, ref: str = "main",
                     owner: str | None = None) -> Union[str, List[Dict[str, Any]]]:
    """Devuelve contenido de archivo o lista directorio."""
    api, env_owner, token = _github_env()
    owner = owner or env_owner
    hdr   = _headers(token)

    url = f"{api}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    rsp = requests.get(url, headers=hdr, timeout=15)
    rsp.raise_for_status()
    content = rsp.json()

    if isinstance(content, list):                   # directorio
        return content

    if content.get("encoding") == "base64":
        return base64.b64decode(content["content"]).decode("utf-8")
    return f"No se pudo decodificar el contenido ({content.get('html_url')})"


def create_pull_request(repo: str, head: str, base: str,
                        title: str, body: str = "",
                        owner: str | None = None) -> Dict[str, Any]:
    """Abre un PR head→base."""
    api, env_owner, token = _github_env()
    owner = owner or env_owner
    hdr   = _headers(token)

    rsp = requests.post(f"{api}/repos/{owner}/{repo}/pulls",
                        headers=hdr,
                        json={"title": title, "body": body, "head": head, "base": base},
                        timeout=15)
    rsp.raise_for_status()
    return rsp.json()


def list_pull_requests(repo: str, state: str = "open",
                       owner: str | None = None) -> List[Dict[str, Any]]:
    """Lista PRs del repo (`state` open/closed/all)."""
    api, env_owner, token = _github_env()
    owner = owner or env_owner
    hdr   = _headers(token)

    rsp = requests.get(f"{api}/repos/{owner}/{repo}/pulls?state={state}&per_page=100",
                       headers=hdr, timeout=15)
    rsp.raise_for_status()
    return rsp.json()
