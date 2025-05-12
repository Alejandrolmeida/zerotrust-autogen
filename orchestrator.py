"""
Orquestador - Gestiona la creación del equipo y la colaboración entre agentes
"""

import textwrap
from typing import Dict

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat


def setup_team(
    github_agent: AssistantAgent,
    policy_agent: AssistantAgent,
    posture_agent: AssistantAgent,
    bicep_agent: AssistantAgent,
    llm_client: AzureOpenAIChatCompletionClient
) -> SelectorGroupChat:
    """Configura el equipo de agentes para la conversación"""
    user_proxy = UserProxyAgent("human")
    
    # Prompt para el selector que decide qué agente debe responder
    selector_prompt = """
    Analiza el historial completo de la conversación y el último mensaje del usuario ⬇️ para determinar el agente más adecuado:
    github_agent · policy_agent · posture_agent · bicep_agent

    • github_agent  - Gestiona operaciones en GitHub: creación de ramas, manejo de PR, workflows CI/CD, y administración de repositorios.
    • policy_agent  - Especialista en Azure Policy: búsqueda, validación, asignación de políticas, y análisis de cumplimiento Zero-Trust.
    • posture_agent - Analiza la postura de seguridad: cálculo de Secure Score, generación de recomendaciones, consultas avanzadas en Resource Graph, y generación de informes de seguridad.
    • bicep_agent   - Diseña y despliega infraestructura: creación de Azure Landing Zones, generación de plantillas Bicep, y ejecución de despliegues.

    Considera el contexto general de la conversación, el tema principal del último mensaje y cualquier información relevante previa. Si el mensaje menciona términos como "postura de seguridad", "Secure Score", "recomendaciones de seguridad" o "Resource Graph", asigna al posture_agent. Si no encaja claramente con ninguno, responde: unknown
    """

    return SelectorGroupChat(
        participants=[user_proxy, github_agent, policy_agent, posture_agent, bicep_agent],
        model_client=llm_client,
        selector_prompt=selector_prompt,
        max_turns=1,
    )
