#!/usr/bin/env python
"""
main.py - Equipo Zero-Trust (GitHub · Policy · Posture · Bicep)

Este script implementa un sistema de agentes conversacionales para ayudar 
en tareas de zero-trust relacionadas con GitHub, Azure Policy, Security Posture
y Azure Landing Zones con Bicep.
"""

from __future__ import annotations
import asyncio
import os
import pathlib
import textwrap
import traceback
from typing import Set

from autogen_agentchat.ui import Console
from autogen_agentchat.teams import SelectorGroupChat

# Importaciones de módulos propios
from config import setup_environment, validate_environment, create_llm_client, setup_tools
from agents.github_agent import create_github_agent
from agents.policy_agent import create_policy_agent
from agents.posture_agent import create_posture_agent
from agents.bicep_agent import create_bicep_agent
from orchestrator import setup_team

# Constantes
EXIT_COMMANDS: Set[str] = {"exit", "salir", "quit", "q"}


async def interactive_loop(team: SelectorGroupChat) -> None:
    """Ejecuta el bucle interactivo principal que procesa los mensajes del usuario"""
    print("💬  Equipo Zero-Trust listo.  Escribe tu pregunta ('salir' para terminar).")
    
    while True:
        text = input("\n📝  Tú: ").strip()
        
        if text.lower() in EXIT_COMMANDS:
            print("👋  ¡Hasta la próxima!")
            break
            
        if not text:
            continue
            
        print("⏳  Procesando…")
        stream = team.run_stream(task=text)  # ejecutar petición
        await Console(stream)  # imprimir salida por defecto


async def main() -> None:
    """Función principal que inicializa y ejecuta el sistema"""
    print("Iniciando configuración...")
    # Configuración inicial
    setup_environment()
    validate_environment()
    
    print("Creando cliente LLM...")
    # Crear cliente LLM
    llm_client = create_llm_client()
    
    print("Configurando herramientas...")
    # Configurar herramientas
    tools = setup_tools()
    
    # Crear agentes especializados
    print("Creando agentes...")
    github_agent = create_github_agent(llm_client, tools["github"])
    print("- GitHub Agent creado")
    policy_agent = create_policy_agent(llm_client, tools["policy"])
    print("- Policy Agent creado")
    posture_agent = create_posture_agent(llm_client, tools["posture"])
    print("- Posture Agent creado")
    try:
        bicep_agent = create_bicep_agent(llm_client, tools["bicep"])
        print("- Bicep Agent creado")
    except Exception as e:
        print(f"Error al crear Bicep Agent: {e}")
        raise
    
    # Configurar equipo
    team = setup_team(
        github_agent=github_agent,
        policy_agent=policy_agent,
        posture_agent=posture_agent,
        bicep_agent=bicep_agent,
        llm_client=llm_client
    )
    
    # Ejecutar loop interactivo
    await interactive_loop(team)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋  Sesión interrumpida.")
    except Exception as exc:
        print(f"\n❌ Error inesperado: {exc}")
        traceback.print_exc()
