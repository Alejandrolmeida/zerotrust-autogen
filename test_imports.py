#!/usr/bin/env python
"""Script de prueba para verificar importaciones"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Intentando importar desde setup...")
    from setup.config import setup_environment, validate_environment
    print("✅ Importación desde setup.config exitosa!")
    
    print("\nIntentando importar desde agents...")
    from agents.github_agent import create_github_agent
    from agents.policy_agent import create_policy_agent
    from agents.posture_agent import create_posture_agent
    print("✅ Importación desde agents exitosa!")
    
    print("\nIntentando importar desde tools...")
    from tools import github_tools, policy_tools, posture_tools
    print("✅ Importación desde tools exitosa!")
    
    print("\nIntentando importar desde orchestrator...")
    from orchestrator import setup_team
    print("✅ Importación desde orchestrator exitosa!")
    
    print("\nTodas las importaciones funcionan correctamente! ✅")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
