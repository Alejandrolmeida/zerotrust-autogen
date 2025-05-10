#!/usr/bin/env python
"""
all_demos/main.py
────────────────────────────────────────────────────────────────────────
Ejecuta los tres agentes (GitHub Agent, Posture Agent, Policy Agent)
en un mismo SelectorGroupChat.  El LLM lee la petición del usuario y
elige con qué agente trabajar.

Requisitos previos
──────────────────
• Variables de entorno (.env raíz):
      # LLM
      AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
      AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION
      # GitHub  / Secure Score / Azure creds … (los mismos de cada demo)

Ejecutar:
    python demo-team/main.py
────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
import asyncio, os, textwrap, sys
from dotenv import load_dotenv

# Añadir el directorio raíz al path de Python
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# ────────── 1)  Cargar variables de entorno ──────────
dotenv_path = os.path.join(root_dir, '.env')
print(f"\n[DEBUG] Cargando variables de entorno desde: {dotenv_path}")
print(f"[DEBUG] El archivo existe: {os.path.exists(dotenv_path)}")
load_dotenv(dotenv_path=dotenv_path)

# Verificar si las variables críticas se cargaron correctamente
critical_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME", 
                "GITHUB_TOKEN", "GITHUB_OWNER"]
print("[DEBUG] Estado de variables críticas:")
for var in critical_vars:
    value = os.getenv(var)
    if value:
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
        print(f"[DEBUG] ✅ {var} cargada: {masked}")
    else:
        print(f"[DEBUG] ❌ {var} no encontrada")

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
# Cambiar importación a mcp_server_tools
from autogen_ext.tools.mcp import mcp_server_tools, SseServerParams

# ────────── 2)  Crear LLM "coordinador" ──────────
llm_client = AzureOpenAIChatCompletionClient(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

SELECTOR_PROMPT = textwrap.dedent("""
    Eres el *dispatcher* de un equipo de agentes especializados:

    1️⃣ **github_agent**  –  Infraestructura como código: genera Bicep/Terraform,
       crea PRs en GitHub y dispara workflows.  Útil para *Landing Zone Express*.

    2️⃣ **posture_agent** –  Seguridad y postura: consulta Secure Score, Azure
       Resource Graph y aplica correcciones ("Auto‑Fix").  Útil en
       *AI Posture Guardian*.

    3️⃣ **policy_agent**  –  Zero Trust: convierte requisitos en Azure Policy,
       valida y asigna.  Útil en *Policy‑as‑Prompt*.

    Analiza la petición del usuario y responde SÓLO con el **nombre del agente
    más adecuado** (github_agent | posture_agent | policy_agent).  Si la
    pregunta no encaja con ninguno, responde "unknown".
""").strip()

# ────────── 3)  Configurar timeout más largo para MCP ──────────
os.environ["MCP_CLIENT_REQUEST_TIMEOUT"] = "60"

# ────────── 4)  Configurar rutas de servidores MCP ──────────
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
github_server_script = os.path.join(current_dir, "mcp_servers", "github_server.py")
posture_server_script = os.path.join(current_dir, "mcp_servers", "posture_server.py")
policy_server_script = os.path.join(current_dir, "mcp_servers", "policy_server.py")

# ────────── 5)  Crear y configurar agentes ──────────
async def build_agents():
    # URL para el servidor MCP Combinado que tiene todas las herramientas
    # Usamos el nuevo puerto 8765 para evitar conflictos
    combined_server_url = "http://localhost:8765/mcp"
    
    # GitHub Agent - conectado al servidor combinado
    github_tools = await mcp_server_tools(SseServerParams(url=combined_server_url, headers={"accept": "text/event-stream"}))
    github_agent = AssistantAgent(
        name="github_agent",
        system_message="""Eres un experto en DevOps e infraestructura como código.
Puedes generar archivos Bicep o Terraform, crear PRs en GitHub y gestionar despliegues.
Eres especialista en automatizar la creación de Landing Zones en Azure.""",
        model_client=llm_client,
        tools=github_tools
    )

    # Posture Agent - conectado al servidor combinado
    posture_tools = await mcp_server_tools(SseServerParams(url=combined_server_url))
    posture_agent = AssistantAgent(
        name="posture_agent",
        system_message="""Eres un experto en seguridad y postura de Azure.
Puedes consultar Secure Score, analizar recursos con Azure Resource Graph y aplicar correcciones.
Tu especialidad es identificar problemas de seguridad y recomendar soluciones.""",
        model_client=llm_client,
        tools=posture_tools
    )

    # Policy Agent - conectado al servidor combinado
    policy_tools = await mcp_server_tools(SseServerParams(url=combined_server_url))
    policy_agent = AssistantAgent(
        name="policy_agent",
        system_message="""Eres un experto en Zero Trust y Azure Policy.
Puedes convertir requisitos en políticas de Azure, validarlas y asignarlas.
Tu especialidad es implementar controles de seguridad basados en principios Zero Trust.""",
        model_client=llm_client,
        tools=policy_tools
    )

    return github_agent, posture_agent, policy_agent

# ────────── 6)  Bucle principal ──────────
EXIT_WORDS = {"exit", "salir", "quit", "q"}

async def main() -> None:
    github, posture, policy = await build_agents()

    team = SelectorGroupChat(
        name="demo_team",
        agents=[github, posture, policy],
        selector_prompt=SELECTOR_PROMPT,
        model_client=llm_client,
    )

    user = UserProxyAgent(name="human")

    print("\n🎬 Team Zero Trust Ready")

    while True:
        prompt = input("📝  Tú: ").strip()
        if prompt.lower() in EXIT_WORDS:
            break
        if not prompt:
            continue

        print("\n⏳  Procesando…")
        # Mensaje del usuario → equipo
        result = await team.run(task=TextMessage(content=prompt, source="human"))

        # Mostrar todas las respuestas que no vengan del system/dispatcher
        for msg in getattr(result, "messages", []):
            if msg.source in {"github_agent", "posture_agent", "policy_agent"}:
                tag = {"github_agent": "GitHub  ", "posture_agent": "Posture ", "policy_agent": "Policy  "}[msg.source]
                print(f"\n🤖  {tag}Agent:\n{msg.content}")

    print("\nHasta la próxima 👋")

# ────────── 7)  Entrada ──────────
if __name__ == "__main__":
    asyncio.run(main())
