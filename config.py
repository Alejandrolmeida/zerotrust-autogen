"""
Configuración para el sistema Zero-Trust

Este módulo contiene las funciones para configurar el entorno
y gestionar la configuración común del sistema.
"""

import os
import pathlib
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from typing import Dict, List, Any


# Constantes
BASE_DIR = pathlib.Path(__file__).parent.resolve()  # Directorio raíz


def setup_environment() -> None:
    """Configura el entorno y carga variables desde .env"""
    load_dotenv(override=True)  # <- fuerza recarga del .env
    
    # Establece timeout por defecto
    os.environ.setdefault("OPENAI_REQUEST_TIMEOUT", "120")


def validate_environment() -> None:
    """Valida que todas las variables de entorno necesarias estén disponibles"""
    env_vars = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
    }
    
    missing = [k for k, v in env_vars.items() if not v]
    if missing:  # abortar si falta algo
        raise SystemExit(f"❌ Faltan variables en .env: {', '.join(missing)}")


def create_llm_client() -> AzureOpenAIChatCompletionClient:
    """Crea y configura el cliente LLM para Azure OpenAI"""
    return AzureOpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        model=os.getenv("AZURE_OPENAI_MODEL_NAME", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


def setup_tools() -> Dict[str, List[Any]]:
    """Configura las herramientas para cada agente"""
    from tools import github_tools as gh
    from tools import policy_tools as pol
    from tools import posture_tools as pos
    from tools import bicep_tools as bicep
    
    tools = {
        "github": [
            gh.create_branch, 
            gh.list_repositories, 
            gh.get_repository,
            gh.get_file_content, 
            gh.create_pull_request, 
            gh.list_pull_requests
        ],
        "policy": [
            pol.get_policy_definition, 
            pol.list_policy_definitions,
            pol.assign_policy, 
            pol.list_policy_assignments
        ],
        "posture": [
            pos.get_secure_score, 
            pos.list_posture_recommendations,
            pos.get_detailed_recommendation
        ],
        "bicep": [
            bicep.generate_landing_zone,
            bicep.deploy_landing_zone
        ]
    }
    
    return tools
