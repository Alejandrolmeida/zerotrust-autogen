#!/usr/bin/env python
"""
MCP‑Server – Herramientas GitHub para 'Landing Zone Express'.
Requiere en .env:  GITHUB_PAT, GITHUB_OWNER
"""
import os, sys
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Ajustar el path para importar mcp_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mcp_tools.github_tools as gh

# Crear dos instancias idénticas para montar en /mcp y /mcp/
mcp = FastMCP("GitHub MCP Server", stateless_http=True)

# Solución avanzada: charset regex
# Creamos un patrón regex que acepte ambas rutas (con o sin barra final)
import re
from fastapi.routing import APIRoute

# Registrar herramientas en ambas instancias FastMCP
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

if __name__ == "__main__":
    port = int(os.environ.get("MCP_GITHUB_PORT", 8001))
    app = FastAPI()
    
    # Montar el MCP Server en /mcp
    app.mount("/mcp", mcp.streamable_http_app())
    
    # Middleware para manejar /mcp/
    from fastapi import Request, status
    from fastapi.responses import Response
    from starlette.middleware.base import BaseHTTPMiddleware

    class MCPSlashMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Si es una petición a /mcp/ (con barra final)
            if request.url.path == "/mcp/":
                # Reusar el mismo app montado en /mcp
                mcp_app = mcp.streamable_http_app()
                # Procesa la petición con el mismo handler de /mcp
                return await mcp_app(request.scope, request._receive, request._send)
            
            # Para cualquier otra URL, continuar con el flujo normal
            return await call_next(request)
            
    # Agregar el middleware
    app.add_middleware(MCPSlashMiddleware)
    
    # Ruta raíz para información
    @app.get("/", include_in_schema=False)
    async def root():
        return Response("MCP server disponible en /mcp", status_code=200)

    print(f"[MCP-GitHub] FastAPI server running on http://localhost:{port}/mcp")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
