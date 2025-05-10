#!/usr/bin/env python
"""
MCP‑Server – Herramientas 'AI Posture Guardian'.
.env: TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID
"""
import os, sys
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# Ajustar el path para importar mcp_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_tools.posture_tools import get_secure_score, query_resource_graph, auto_fix_recommendation

# Crear instancia de FastMCP
mcp = FastMCP("Posture MCP Server", stateless_http=True)

# Registrar herramientas
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
    port = int(os.environ.get("MCP_POSTURE_PORT", 8003))
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

    print(f"[MCP-Posture] FastAPI server running on http://localhost:{port}/mcp")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
