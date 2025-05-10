"""
Policy Agent - Agente especializado en Azure Policy
"""

import textwrap
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from typing import List, Any


def create_policy_agent(llm_client: AzureOpenAIChatCompletionClient, policy_tools: List[Any]) -> AssistantAgent:
    """Crea y configura el agente especialista en Azure Policy"""
    
    return AssistantAgent(
        "policy_agent",
        system_message=textwrap.dedent("""
            Eres un **Azure Policy Expert**. Buscas, validas y asignas políticas
            Zero‑Trust. Respuestas concisas en español.
        """).strip(),
        model_client=llm_client,
        tools=policy_tools,
    )
