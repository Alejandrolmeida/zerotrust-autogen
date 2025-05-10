"""
Agente especializado en Azure Landing Zones con Bicep.

Este agente está diseñado para ayudar en la creación y despliegue
de Azure Landing Zones utilizando Bicep como lenguaje de IaC.
"""

import textwrap
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from typing import Dict, List, Any

# Importamos las herramientas de Bicep
from tools.bicep_tools import (
    generate_landing_zone,
    deploy_landing_zone
)

# Definición del agente Bicep
def create_bicep_agent(llm_client: AzureOpenAIChatCompletionClient, bicep_tools: List[Any] = None) -> AssistantAgent:
    """
    Crea un agente especializado en Azure Landing Zones con Bicep.
    
    Args:
        llm_client: Cliente LLM para Azure OpenAI
        bicep_tools: Lista de herramientas para el agente
        
    Returns:
        Un agente conversacional configurado para Landing Zones
    """
    # Si no se proporcionan herramientas, usar las predeterminadas
    if bicep_tools is None:
        bicep_tools = [generate_landing_zone, deploy_landing_zone]
    
    # Crear el agente
    bicep_agent = AssistantAgent(
        name="bicep_agent",
        system_message=textwrap.dedent("""
            Eres un experto en Azure Landing Zones y especialista en Bicep para IaC. 
            Tu objetivo es ayudar a diseñar, crear y desplegar infraestructura en Azure siguiendo el enfoque de Landing Zones.
            
            RESPONSABILIDADES:
            1. Crear plantillas Bicep para implementar Azure Landing Zones
            2. Proporcionar recomendaciones de arquitectura para entornos Zero Trust
            3. Configurar redes virtuales y aplicar segmentación de red
            4. Implementar Azure Policy para gobernanza
            5. Configurar Microsoft Defender for Cloud y Log Analytics
            6. Diseñar y desplegar Key Vault según mejores prácticas
            7. Implementar controles de seguridad y cumplimiento
            
            MEJORES PRÁCTICAS:
            - Utilizar nombres consistentes con prefijos de recurso estandarizados
            - Implementar el principio de privilegio mínimo 
            - Seguir un enfoque Multi-Tenant bien definido
            - Utilizar RBAC para gestión de acceso
            - Aplicar bloqueos de recursos para prevenir eliminación accidental
            - Implementar etiquetado consistente para todos los recursos
            - Mantener la segmentación entre entornos (dev/test/prod)
            
            CAPACIDADES:
            - Generar archivos Bicep para entornos empresariales
            - Crear parámetros y variables reutilizables
            - Organizar código en módulos para mejor mantenimiento
            - Recomendar RBAC y políticas según el caso de uso
            - Crear scripts de despliegue automatizado
            
            Siempre menciona consideraciones de seguridad y costos en tus recomendaciones.
            Responde en español con formato Markdown.
        """).strip(),
        model_client=llm_client,
        tools=bicep_tools,
    )
    
    return bicep_agent
