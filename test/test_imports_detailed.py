#!/usr/bin/env python
"""
Script para probar diferentes formas de importación
"""

import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

def test_import(module_name):
    print(f"\nIntentando importar: {module_name}")
    try:
        __import__(module_name)
        print(f"✓ Importación exitosa: {module_name}")
        return True
    except ImportError as e:
        print(f"✗ Error importando {module_name}: {e}")
        return False

# Probar diferentes variantes de nombres de módulos
modules_to_test = [
    'autogen_agentchat',
    'autogen-agentchat',
    'autogen_ext',
    'autogen-ext',
    'autogen_ext.models',
    'autogen-ext.models',
    'autogenext',
    'autogenchat',
    'autogen.agentchat',
    'autogen.ext'
]

for module in modules_to_test:
    test_import(module)

print("\nListando paquetes instalados:")
try:
    import pkg_resources
    packages = [p.key for p in pkg_resources.working_set]
    for p in sorted(packages):
        if 'auto' in p.lower():
            print(f"- {p}")
except Exception as e:
    print(f"Error listando paquetes: {e}")
