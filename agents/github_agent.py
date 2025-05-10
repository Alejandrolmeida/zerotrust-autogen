"""
GitHub Agent - Agente especializado en operaciones de GitHub
"""

import textwrap
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from typing import List, Any


def create_github_agent(llm_client: AzureOpenAIChatCompletionClient, github_tools: List[Any]) -> AssistantAgent:
    """Crea y configura el agente especialista en GitHub"""
    
    return AssistantAgent(
        "github_agent",
        system_message=textwrap.dedent("""
            Eres un **DevOps GitHub Expert**. Gestionas ramas, PR y contenido
            de repositorios. Responde en español con Markdown breve.
        """).strip(),
        model_client=llm_client,
        tools=github_tools,
    )
