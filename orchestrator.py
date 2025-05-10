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
    llm_client: AzureOpenAIChatCompletionClient
) -> SelectorGroupChat:
    """Configura el equipo de agentes para la conversación"""
    user_proxy = UserProxyAgent("human")
    
    # Prompt para el selector que decide qué agente debe responder
    selector_prompt = """
    Lee SOLO el último mensaje del usuario ⬇️ y contesta con **un** nombre:
    github_agent · policy_agent · posture_agent

    • github_agent  - temas: GitHub, repos, ramas, PR, workflows.
    • policy_agent  - temas: Azure Policy, definición, asignación, cumplimiento.
    • posture_agent - temas: Secure Score, recomendaciones, Resource Graph.

    Si no encaja, devuelve: unknown
    """

    return SelectorGroupChat(
        participants=[user_proxy, github_agent, policy_agent, posture_agent],
        model_client=llm_client,
        selector_prompt=selector_prompt,
        max_turns=3,
    )
