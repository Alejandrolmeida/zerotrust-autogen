"""
Posture Agent - Agente especializado en análisis de seguridad
"""

import textwrap
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from typing import List, Any


def create_posture_agent(llm_client: AzureOpenAIChatCompletionClient, posture_tools: List[Any]) -> AssistantAgent:
    """Crea y configura el agente especialista en Security Posture"""
    
    return AssistantAgent(
        "posture_agent",
        system_message=textwrap.dedent("""
            Eres un **Security Posture Analyst**. Trabajas con Secure Score,
            recomendaciones y Resource Graph. Responde claro en español.
        """).strip(),
        model_client=llm_client,
        tools=posture_tools,
    )
