#!/usr/bin/env python
"""
MCP‑Server Combinado – Proporciona todas las herramientas en un único servidor.
Solución para el problema de la barra final en URLs de MCP.
"""
import os
import sys
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Ajustar el path para importar mcp_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar todas las herramientas
import mcp_tools.github_tools as gh
from mcp_tools.policy_tools import validate_policy, assign_policy
from mcp_tools.posture_tools import get_secure_score, query_resource_graph, auto_fix_recommendation

# Crear un único FastMCP que contendrá todas las herramientas
# El parámetro stateless_http=True es necesario para el modo HTTP
mcp = FastMCP("Unified LZE MCP Server", stateless_http=True)

# ================= GitHub Tools =================
@mcp.tool(name="create_branch", description="Crea una rama desde el branch por defecto.")
def create_branch(repo: str, new_branch: str) -> dict:
    return gh.create_branch_from_default(repo, new_branch)

@mcp.tool(name="commit_files", description="Añade / actualiza ficheros en una rama.")
def commit_files(repo: str, branch: str, files: dict, message: str) -> dict:
    return gh.commit_files_to_branch(repo, branch, files, message)

@mcp.tool(name="create_pull_request", description="Abre un PR entre dos ramas.")
def create_pr(repo: str, head: str, base: str, title: str, body: str = "") -> dict:
    return gh.create_pull_request(repo, head, base, title, body)

@mcp.tool(name="trigger_workflow", description="Lanza manualmente un workflow_dispatch.")
def trigger_workflow(repo: str, workflow: str, ref: str, inputs: dict = None) -> dict:
    if inputs is None:
        inputs = {}
    return gh.trigger_workflow_run(repo, workflow, ref, inputs)

# ================= Policy Tools =================
@mcp.tool(name="validate_policy_json", description="Valida sintaxis básica de un Azure Policy JSON.")
def validate_policy_json(policy: dict) -> dict:
    return validate_policy(policy)

@mcp.tool(name="assign_policy", description="Asigna (o reemplaza) un Azure Policy en el scope indicado.")
def assign_policy_tool(policy: dict, scope: str, name: str = "") -> dict:
    return assign_policy(policy, scope, name)

# ================= Posture Tools =================
@mcp.tool(name="get_secure_score", description="Devuelve Secure Score completo.")
def get_secure_score_tool() -> dict:
    return get_secure_score()

@mcp.tool(name="query_resource_graph", description="Ejecución libre de Azure Resource Graph (Kusto-like).")
def query_resource_graph_tool(query: str) -> dict:
    return query_resource_graph(query)

@mcp.tool(name="auto_fix_recommendation", description="Ejecuta un auto-fix (simplificado) sobre una recomendación Defender.")
def auto_fix_recommendation_tool(recommendation_id: str) -> dict:
    return auto_fix_recommendation(recommendation_id)

if __name__ == "__main__":
    # Usar un puerto diferente para evitar conflictos
    port = int(os.environ.get("MCP_PORT", 8765))
    
    # Enfoque estándar de FastAPI con endpoint MCP
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    # Montar la aplicación MCP en el endpoint /mcp
    mcp_app = mcp.streamable_http_app()
    app.mount("/mcp", mcp_app)
    
    # Ruta informativa en la raíz
    @app.get("/")
    async def root():
        return JSONResponse({
            "name": "LZE Combined MCP Server",
            "status": "running",
            "endpoint": "/mcp"
        })
    
    # Inicio del servidor
    print(f"[MCP-Combined] FastAPI server running on http://localhost:{port}/mcp")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
