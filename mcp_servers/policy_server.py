#!/usr/bin/env python
"""
MCP‑Server – Herramientas 'Policy‑as‑Prompt'.
.env: TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID
"""
import os, sys
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Ajustar el path para importar mcp_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_tools.policy_tools import validate_policy, assign_policy

# Crear instancia de FastMCP
mcp = FastMCP("Policy MCP Server", stateless_http=True)

# Registrar herramientas
@mcp.tool(name="validate_policy_json", description="Valida sintaxis básica de un Azure Policy JSON.")
def validate_policy_json(policy: dict) -> dict:
    return validate_policy(policy)

@mcp.tool(name="assign_policy", description="Asigna (o reemplaza) un Azure Policy en el scope indicado.")
def assign_policy_tool(policy: dict, scope: str, name: str = "") -> dict:
    return assign_policy(policy, scope, name)

if __name__ == "__main__":
    port = int(os.environ.get("MCP_POLICY_PORT", 8002))
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

    print(f"[MCP-Policy] FastAPI server running on http://localhost:{port}/mcp")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
