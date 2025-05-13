#!/usr/bin/env python
"""
Script de diagnóstico para identificar problemas en el sistema
"""

import sys
import traceback

def check_imports():
    try:
        import autogen
        print("✅ autogen importado correctamente")
    except Exception as e:
        print(f"❌ Error al importar autogen: {e}")
        traceback.print_exc()

    try:
        from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
        print("✅ AzureOpenAIChatCompletionClient importado correctamente")
    except Exception as e:
        print(f"❌ Error al importar AzureOpenAIChatCompletionClient: {e}")
        traceback.print_exc()

    try:
        from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
        print("✅ UserProxyAgent y AssistantAgent importados correctamente")
    except Exception as e:
        print(f"❌ Error al importar UserProxyAgent/AssistantAgent: {e}")
        traceback.print_exc()

    try:
        from autogen_agentchat.teams import SelectorGroupChat
        print("✅ SelectorGroupChat importado correctamente")
    except Exception as e:
        print(f"❌ Error al importar SelectorGroupChat: {e}")
        traceback.print_exc()

def check_bicep_agent():
    try:
        from agents.bicep_agent import create_bicep_agent
        print("✅ create_bicep_agent importado correctamente")
    except Exception as e:
        print(f"❌ Error al importar create_bicep_agent: {e}")
        traceback.print_exc()

def check_bicep_tools():
    try:
        from tools.bicep_tools import generate_landing_zone, deploy_landing_zone
        print("✅ bicep_tools importado correctamente")
    except Exception as e:
        print(f"❌ Error al importar bicep_tools: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Diagnóstico de importaciones:")
    check_imports()
    
    print("\n🔍 Diagnóstico de bicep_agent:")
    check_bicep_agent()
    
    print("\n🔍 Diagnóstico de bicep_tools:")
    check_bicep_tools()
