"""
Herramientas para la creación y despliegue de Azure Landing Zones con Bicep.

Este módulo proporciona funciones para generar plantillas Bicep de
Landing Zones y desplegarlas en Azure.
"""

import os
import subprocess
import json
from typing import Dict, List, Optional, Any
import pathlib

from config import BASE_DIR

# Ruta a la carpeta de infraestructura
INFRA_DIR = BASE_DIR / "Infra"

def generate_landing_zone(
    organization_name: str,
    environment: str = "prod",
    regions: List[str] = ["westeurope"],
    include_networking: bool = True,
    include_security: bool = True,
    include_governance: bool = True,
) -> Dict[str, Any]:
    """
    Genera una landing zone básica empresarial en Bicep.
    
    Args:
        organization_name: Nombre de la organización
        environment: Entorno de despliegue (dev, test, prod)
        regions: Lista de regiones donde desplegar
        include_networking: Incluir recursos de red
        include_security: Incluir recursos de seguridad
        include_governance: Incluir recursos de gobernanza
    
    Returns:
        Dict con información sobre los archivos generados
    """
    os.makedirs(INFRA_DIR, exist_ok=True)
    
    generated_files = []
    
    # Generar archivo main.bicep
    main_bicep_path = INFRA_DIR / "main.bicep"
    with open(main_bicep_path, "w") as f:
        f.write(_generate_main_bicep(
            organization_name=organization_name,
            environment=environment,
            regions=regions,
            include_networking=include_networking,
            include_security=include_security,
            include_governance=include_governance
        ))
    generated_files.append(main_bicep_path)
    
    # Generar archivo de parámetros
    params_path = INFRA_DIR / "main.parameters.json"
    with open(params_path, "w") as f:
        f.write(_generate_parameters_file(
            organization_name=organization_name,
            environment=environment,
            regions=regions
        ))
    generated_files.append(params_path)
    
    # Generar módulos específicos
    if include_networking:
        network_path = INFRA_DIR / "modules" / "networking.bicep"
        os.makedirs(INFRA_DIR / "modules", exist_ok=True)
        with open(network_path, "w") as f:
            f.write(_generate_networking_module(regions))
        generated_files.append(network_path)
    
    if include_security:
        security_path = INFRA_DIR / "modules" / "security.bicep"
        os.makedirs(INFRA_DIR / "modules", exist_ok=True)
        with open(security_path, "w") as f:
            f.write(_generate_security_module())
        generated_files.append(security_path)
    
    if include_governance:
        governance_path = INFRA_DIR / "modules" / "governance.bicep"
        os.makedirs(INFRA_DIR / "modules", exist_ok=True)
        with open(governance_path, "w") as f:
            f.write(_generate_governance_module(organization_name, environment))
        generated_files.append(governance_path)
    
    # Generar script de despliegue
    deploy_script_path = INFRA_DIR / "deploy_landing_zone.sh"
    with open(deploy_script_path, "w") as f:
        f.write(generate_deployment_script())
    os.chmod(deploy_script_path, 0o755)
    generated_files.append(deploy_script_path)
    
    # Retornar solo los nombres de los archivos generados
    return {
        "message": "Landing Zone generada con éxito",
        "generated_files": [str(file.name) for file in generated_files],
        "organization": organization_name,
        "environment": environment,
        "infra_dir": str(INFRA_DIR)
    }


def deploy_landing_zone(
    subscription_id: str,
    resource_group_name: str = None,
    location: str = "westeurope",
    parameters: Dict[str, Any] = None,
    what_if: bool = True  # Por defecto solo muestra cambios sin desplegar
) -> Dict[str, Any]:
    """
    Despliega una landing zone en Azure usando la CLI de Azure.
    
    Args:
        subscription_id: ID de la suscripción donde desplegar
        resource_group_name: Nombre del grupo de recursos (opcional)
        location: Región donde desplegar
        parameters: Parámetros adicionales para el despliegue
        what_if: Si es True, solo muestra los cambios sin desplegar
    
    Returns:
        Dict con información sobre el resultado del despliegue
    """
    # Verificar que existen los archivos necesarios
    main_bicep_path = INFRA_DIR / "main.bicep"
    params_path = INFRA_DIR / "main.parameters.json"
    
    if not main_bicep_path.exists() or not params_path.exists():
        return {
            "error": "No se encontraron los archivos necesarios para el despliegue",
            "required_files": [str(main_bicep_path), str(params_path)]
        }
    
    # Preparar comandos de Azure CLI
    commands = []
    
    # Seleccionar la suscripción
    commands.append(f"az account set --subscription {subscription_id}")
    
    # Crear el grupo de recursos si no se proporciona uno
    if not resource_group_name:
        # Extraer parámetros para nombrar el grupo de recursos
        try:
            with open(params_path, "r") as f:
                param_data = json.load(f)
                org_name = param_data.get("parameters", {}).get("organizationName", {}).get("value", "org")
                env_name = param_data.get("parameters", {}).get("environmentName", {}).get("value", "prod")
                resource_group_name = f"rg-{org_name}-{env_name}-core"
        except Exception:
            resource_group_name = "rg-landingzone-deployment"
        
        commands.append(f"az group create --name {resource_group_name} --location {location}")
    
    # Construir comando de despliegue
    deploy_cmd = f"az deployment group {'what-if' if what_if else 'create'} --resource-group {resource_group_name} --template-file {main_bicep_path} --parameters {params_path}"
    
    # Añadir parámetros adicionales si se proporcionan
    if parameters:
        for key, value in parameters.items():
            deploy_cmd += f" --parameters {key}={value}"
    
    commands.append(deploy_cmd)
    
    # Ejecutar los comandos
    results = []
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
            results.append({"command": cmd, "stdout": result.stdout, "success": True})
        except subprocess.CalledProcessError as e:
            results.append({"command": cmd, "stderr": e.stderr, "success": False})
            # Si falla, detener la ejecución
            return {
                "error": f"Error en el comando: {cmd}",
                "details": e.stderr,
                "results": results
            }
    
    return {
        "message": "Despliegue completado con éxito" if not what_if else "Previsualización del despliegue completada",
        "resource_group": resource_group_name,
        "location": location,
        "results": results,
        "what_if": what_if
    }


def generate_deployment_script() -> str:
    """
    Genera un script de Azure CLI para desplegar la Landing Zone.

    Returns:
        Ruta del archivo del script generado.
    """
    script_content = """#!/bin/bash
# Script para desplegar la Landing Zone

set -e

# Variables
RESOURCE_GROUP="landing-zone-rg"
LOCATION="westeurope"

# Crear grupo de recursos
az group create --name $RESOURCE_GROUP --location $LOCATION

# Desplegar plantillas Bicep
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file main.bicep \
  --parameters @main.parameters.json
"""

    script_path = INFRA_DIR / "deploy_landing_zone.sh"
    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)  # Hacer ejecutable el script

    return str(script_path)


# Funciones auxiliares privadas
def _generate_main_bicep(organization_name, environment, regions, include_networking, include_security, include_governance):
    """Genera el contenido del archivo main.bicep"""
    return f'''// main.bicep - Landing Zone for {organization_name} ({environment})
// Generated automatically for Zero-Trust project

targetScope = 'resourceGroup'

// Parameters
@description('Name of the organization')
param organizationName string = '{organization_name}'

@description('Deployment environment name')
@allowed([
  'dev'
  'test'
  'prod'
])
param environmentName string = '{environment}'

@description('Primary Azure region for resource deployment')
param location string = resourceGroup().location

@description('Tagging object for resource tagging')
param tags object = {{
  environment: environmentName
  applicationName: 'LandingZone'
  organizationName: organizationName
  createdBy: 'ZeroTrustAutomation'
}}

// Variables
var resourceToken = toLower(uniqueString(subscription().id, environmentName, organizationName))

// Resource Group tagging
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' existing = {{
  name: resourceGroup().name
}}

resource rgTags 'Microsoft.Resources/tags@2021-04-01' = {{
  name: 'default'
  scope: rg
  properties: {{
    tags: tags
  }}
}}

// Modules
{f"module networking 'modules/networking.bicep' = {{\n  name: 'networking-deployment'\n  params: {{\n    location: location\n    environmentName: environmentName\n    organizationName: organizationName\n    resourceToken: resourceToken\n    tags: tags\n  }}\n}}" if include_networking else '// Networking module disabled'}

{f"module security 'modules/security.bicep' = {{\n  name: 'security-deployment'\n  params: {{\n    location: location\n    environmentName: environmentName\n    organizationName: organizationName\n    resourceToken: resourceToken\n    tags: tags\n  }}\n}}" if include_security else '// Security module disabled'}

{f"module governance 'modules/governance.bicep' = {{\n  name: 'governance-deployment'\n  params: {{\n    location: location\n    environmentName: environmentName\n    organizationName: organizationName\n    resourceToken: resourceToken\n    tags: tags\n  }}\n}}" if include_governance else '// Governance module disabled'}

// Outputs
output resourceGroupId string = resourceGroup().id
output deploymentName string = deployment().name
{f"output vnetId string = networking.outputs.vnetId" if include_networking else ''}
'''


def _generate_parameters_file(organization_name, environment, regions):
    """Genera el contenido del archivo de parámetros"""
    return f'''{{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {{
    "organizationName": {{
      "value": "{organization_name}"
    }},
    "environmentName": {{
      "value": "{environment}"
    }},
    "location": {{
      "value": "{regions[0]}"
    }},
    "tags": {{
      "value": {{
        "environment": "{environment}",
        "applicationName": "LandingZone",
        "organizationName": "{organization_name}",
        "createdBy": "ZeroTrustAutomation"
      }}
    }}
  }}
}}
'''


def _generate_networking_module(regions):
    """Genera el contenido del módulo de networking.bicep"""
    return f'''// networking.bicep - Networking resources for Landing Zone
// Generated automatically for Zero-Trust project

param location string
param organizationName string
param environmentName string
param resourceToken string
param tags object

// Networking parameters
param vnetAddressPrefix string = '10.0.0.0/16'
param defaultSubnetPrefix string = '10.0.1.0/24'
param privateEndpointSubnetPrefix string = '10.0.2.0/24'
param bastionSubnetPrefix string = '10.0.3.0/27'

// Resources
resource nsg 'Microsoft.Network/networkSecurityGroups@2021-05-01' = {{
  name: 'nsg-${{resourceToken}}'
  location: location
  tags: tags
  properties: {{
    securityRules: [
      {{
        name: 'AllowVnetInbound'
        properties: {{
          description: 'Allow inbound traffic from VNet'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }}
      }}
    ]
  }}
}}

resource vnet 'Microsoft.Network/virtualNetworks@2021-05-01' = {{
  name: 'vnet-${{resourceToken}}'
  location: location
  tags: tags
  properties: {{
    addressSpace: {{
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }}
    subnets: [
      {{
        name: 'snet-default'
        properties: {{
          addressPrefix: defaultSubnetPrefix
          networkSecurityGroup: {{
            id: nsg.id
          }}
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }}
      }}
      {{
        name: 'snet-private-endpoints'
        properties: {{
          addressPrefix: privateEndpointSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }}
      }}
      {{
        name: 'AzureBastionSubnet'
        properties: {{
          addressPrefix: bastionSubnetPrefix
          networkSecurityGroup: {{
            id: nsg.id
          }}
        }}
      }}
    ]
  }}
}}

// Optional: Azure Bastion
resource bastionPublicIp 'Microsoft.Network/publicIPAddresses@2021-05-01' = {{
  name: 'pip-bastion-${{resourceToken}}'
  location: location
  tags: tags
  sku: {{
    name: 'Standard'
  }}
  properties: {{
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
    dnsSettings: {{
      domainNameLabel: '${{toLower(organizationName)}}${{toLower(environmentName)}}bastion'
    }}
  }}
}}

resource bastion 'Microsoft.Network/bastionHosts@2021-05-01' = {{
  name: 'bastion-${{resourceToken}}'
  location: location
  tags: tags
  properties: {{
    ipConfigurations: [
      {{
        name: 'IpConf'
        properties: {{
          subnet: {{
            id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'AzureBastionSubnet')
          }}
          publicIPAddress: {{
            id: bastionPublicIp.id
          }}
        }}
      }}
    ]
  }}
}}

// Outputs
output vnetId string = vnet.id
output vnetName string = vnet.name
output defaultSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'snet-default')
output privateEndpointsSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'snet-private-endpoints')
'''


def _generate_security_module():
    """Genera el contenido del módulo de security.bicep"""
    return '''// security.bicep - Security resources for Landing Zone
// Generated automatically for Zero-Trust project

param location string
param organizationName string
param environmentName string
param resourceToken string
param tags object

// Security parameters
param logRetentionInDays int = 90
param enableDiagnostics bool = true

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: 'log-${resourceToken}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: logRetentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2021-11-01-preview' = {
  name: 'kv-${substring(resourceToken, 0, 16)}'
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: []
    }
  }
}

// Microsoft Defender for Cloud
resource defenderForCloud 'Microsoft.Security/pricings@2022-03-01' = {
  name: 'VirtualMachines'
  properties: {
    pricingTier: 'Standard'
  }
}

resource defenderForStorage 'Microsoft.Security/pricings@2022-03-01' = {
  name: 'StorageAccounts'
  properties: {
    pricingTier: 'Standard'
  }
}

resource defenderForAppServices 'Microsoft.Security/pricings@2022-03-01' = {
  name: 'AppServices'
  properties: {
    pricingTier: 'Standard'
  }
}

resource defenderForKeyVaults 'Microsoft.Security/pricings@2022-03-01' = {
  name: 'KeyVaults'
  properties: {
    pricingTier: 'Standard'
  }
}

// Diagnostics settings for Key Vault if enabled
resource keyVaultDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableDiagnostics) {
  name: 'diag-${keyVault.name}'
  scope: keyVault
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        category: 'AuditEvent'
        enabled: true
        retentionPolicy: {
          days: logRetentionInDays
          enabled: true
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          days: logRetentionInDays
          enabled: true
        }
      }
    ]
  }
}

// Outputs
output logAnalyticsId string = logAnalytics.id
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
'''


def _generate_governance_module(organization_name, environment):
    """Genera el contenido del módulo de governance.bicep"""
    return f'''// governance.bicep - Governance resources for Landing Zone
// Generated automatically for Zero-Trust project

param location string
param organizationName string
param environmentName string
param resourceToken string
param tags object

// Resource Groups variables
var resourceGroups = [
  {{
    name: 'rg-${{organizationName}}-${{environmentName}}-network'
    location: location
    tags: union(tags, {{
      layer: 'networking'
    }})
  }}
  {{
    name: 'rg-${{organizationName}}-${{environmentName}}-security'
    location: location
    tags: union(tags, {{
      layer: 'security'
    }})
  }}
  {{
    name: 'rg-${{organizationName}}-${{environmentName}}-mgmt'
    location: location
    tags: union(tags, {{
      layer: 'management'
    }})
  }}
]

// Policy Assignment
resource policyAssignment 'Microsoft.Authorization/policyAssignments@2020-09-01' = {{
  name: 'pa-${{resourceToken}}'
  location: location
  properties: {{
    displayName: 'Landing Zone Security Standards'
    policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8' // Azure Security Benchmark
    parameters: {{}}
  }}
}}

// Resource Groups - Skip creation at module level, should be created separately
output resourceGroupNames array = [for rg in resourceGroups: rg.name]

// Outputs
output policyAssignmentId string = policyAssignment.id
'''


def _generate_readme(organization_name, environment):
    """Genera el contenido del archivo README.md"""
    return f'''# Azure Landing Zone for {organization_name} - {environment.upper()}

Este directorio contiene la infraestructura como código (IaC) implementada con Bicep para la Landing Zone de {organization_name} en el entorno {environment.upper()}.

## Estructura de archivos

- **main.bicep**: Plantilla principal que organiza toda la implementación
- **main.parameters.json**: Parámetros de despliegue 
- **modules/**: Carpeta de módulos Bicep
  - **networking.bicep**: Recursos de red (VNet, subnets, NSG, etc.)
  - **security.bicep**: Recursos de seguridad (Key Vault, Log Analytics, etc.)
  - **governance.bicep**: Recursos de gobernanza (Políticas, grupos de recursos, etc.)
- **deploy.sh**: Script para desplegar la infraestructura

## Cómo desplegar

Para desplegar esta landing zone, ejecute:

```bash
# Ver cambios sin desplegar
./deploy.sh --what-if

# Desplegar la infraestructura
./deploy.sh
```

## Componentes desplegados

- **Red**: Red virtual con subredes segmentadas y Bastion
- **Seguridad**: Key Vault, Log Analytics y Microsoft Defender for Cloud
- **Gobernanza**: Asignación de políticas básicas de seguridad

## Personalización

Puede personalizar el despliegue editando el archivo `main.parameters.json`.

## Notas

Esta landing zone fue generada automáticamente por el agente Zero-Trust.
'''


def _generate_deploy_script(organization_name, environment):
    """Genera el script de despliegue"""
    return f'''#!/bin/bash
# Script para desplegar la landing zone de {organization_name} ({environment})

set -e

# Variables
INFRA_DIR=$(dirname "$0")
RG_NAME=""
LOCATION="westeurope"
SUBSCRIPTION_ID=""
WHAT_IF=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
  case $1 in
    --subscription|-s)
      SUBSCRIPTION_ID="$2"
      shift 2
      ;;
    --resource-group|-g)
      RG_NAME="$2"
      shift 2
      ;;
    --location|-l)
      LOCATION="$2"
      shift 2
      ;;
    --what-if)
      WHAT_IF=true
      shift
      ;;
    --help|-h)
      echo "Uso: $0 [opciones]"
      echo ""
      echo "Opciones:"
      echo "  --subscription, -s ID      ID de la suscripción"
      echo "  --resource-group, -g RG    Nombre del grupo de recursos"
      echo "  --location, -l LOC         Ubicación (por defecto: westeurope)"
      echo "  --what-if                  Mostrar cambios sin desplegar"
      echo "  --help, -h                 Mostrar esta ayuda"
      exit 0
      ;;
    *)
      echo "Opción desconocida: $1"
      exit 1
      ;;
  esac
done

# Verificar si estamos logueados en Azure
echo "Verificando acceso a Azure..."
az account show &> /dev/null || {{ echo "No se ha iniciado sesión en Azure. Ejecute 'az login' primero"; exit 1; }}

# Obtener la suscripción automáticamente si no se especificó
if [[ -z "$SUBSCRIPTION_ID" ]]; then
  echo "Seleccionando suscripción predeterminada..."
  SUBSCRIPTION_ID=$(az account show --query id -o tsv)
else
  # Establecer la suscripción especificada
  echo "Seleccionando suscripción $SUBSCRIPTION_ID..."
  az account set --subscription "$SUBSCRIPTION_ID"
fi

echo "Usando suscripción: $(az account show --query name -o tsv)"

# Extraer parámetros del archivo de parámetros
if [[ -f "$INFRA_DIR/main.parameters.json" ]]; then
  ORG_NAME=$(jq -r '.parameters.organizationName.value' "$INFRA_DIR/main.parameters.json")
  ENV_NAME=$(jq -r '.parameters.environmentName.value' "$INFRA_DIR/main.parameters.json")
  
  # Si no se especificó un grupo de recursos, crear uno basado en los parámetros
  if [[ -z "$RG_NAME" ]]; then
    RG_NAME="rg-${{ORG_NAME}}-${{ENV_NAME}}-core"
    echo "Usando grupo de recursos generado: $RG_NAME"
  fi
else
  echo "No se encontró archivo de parámetros en $INFRA_DIR/main.parameters.json"
  
  # Usar un grupo de recursos predeterminado si no se especificó
  if [[ -z "$RG_NAME" ]]; then
    RG_NAME="rg-landingzone-deployment"
    echo "Usando grupo de recursos predeterminado: $RG_NAME"
  fi
fi

# Crear el grupo de recursos si no existe
if ! az group show --name "$RG_NAME" &> /dev/null; then
  echo "Creando grupo de recursos $RG_NAME en $LOCATION..."
  az group create --name "$RG_NAME" --location "$LOCATION"
else
  echo "Usando grupo de recursos existente: $RG_NAME"
fi

# Preparar el comando de despliegue
DEPLOY_CMD="az deployment group"

if [[ "$WHAT_IF" == true ]]; then
  DEPLOY_CMD+=" what-if"
  echo "Mostrando cambios sin desplegar..."
else
  DEPLOY_CMD+=" create"
  echo "Iniciando despliegue..."
fi

# Ejecutar el despliegue
$DEPLOY_CMD \\
  --resource-group "$RG_NAME" \\
  --template-file "$INFRA_DIR/main.bicep" \\
  --parameters "$INFRA_DIR/main.parameters.json"

# Si fue un despliegue real (no what-if), mostrar recursos creados
if [[ "$WHAT_IF" != true ]]; then
  echo ""
  echo "Despliegue completado. Recursos creados:"
  az resource list --resource-group "$RG_NAME" --output table
fi

echo ""
echo "Proceso finalizado."
'''
