// -----------------------------------------------------------------------------
// Landing‑Zone Express – recursos básicos para la demo
//   1. Log Analytics Workspace
//   2. Activación de Microsoft Sentinel
//   3. Playbook (Logic App) disparable a mano
// -----------------------------------------------------------------------------

@description('Nombre del Log Analytics Workspace')
param workspaceName string = 'demo-la'

@description('Nombre de la Logic App (playbook) que usarás desde el agente')
param playbookName string = 'pb-isolate-vm'

@description('Región donde desplegar (westeurope, northeurope, …)')
param location string = resourceGroup().location

// ──────────────────────────────────────────────────────────────────────────────
// 1.  Log Analytics
// ──────────────────────────────────────────────────────────────────────────────
resource la 'Microsoft.OperationalInsights/workspaces@2023-04-01' = {
  name:  workspaceName
  location: location
  sku: {
    name: 'PerGB2018'
  }
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 2.  Activar Microsoft Sentinel en el workspace
//    → basta con crear el provider “MicrosoftSecurityInsights”
// ──────────────────────────────────────────────────────────────────────────────
resource sentinel 'Microsoft.OperationalInsights/workspaces/providers@2022-10-01-preview' = {
  name:  '${la.name}/MicrosoftSecurityInsights'
  // no se necesitan propiedades: la existencia del recurso habilita Sentinel
}

// ──────────────────────────────────────────────────────────────────────────────
// 3.  Logic App (playbook) – gatillo HTTP manual
//    plantilla ultraligera para la demo; añade acciones si lo necesitas
// ──────────────────────────────────────────────────────────────────────────────
resource playbook 'Microsoft.Logic/workflows@2019-05-01' = {
  name:     playbookName
  location: location
  tags: {
    purpose: 'demo-landzone-express'
  }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2019-05-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      triggers: {
        manual: {
          type: 'Request'
          kind: 'Http'
          inputs: {
            schema: {}      // sin esquema → acepta cualquier JSON
          }
        }
      }
      actions: {
        respond: {
          type: 'Response'
          kind: 'Http'
          inputs: {
            statusCode: 200
            body: {
              message: 'Playbook ejecutado correctamente'
            }
          }
          runAfter: {}
        }
      }
    }
  }
  // concedemos a la Logic App permiso para lanzarse a sí misma vía REST
  identity: {
    type: 'SystemAssigned'
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// 4.  Salidas útiles para el script de la demo
// ──────────────────────────────────────────────────────────────────────────────
output workspaceId   string = la.id
output sentinelName  string = sentinel.name
output playbookId    string = playbook.id
output playbookURL   string = 'https://portal.azure.com/#view/Microsoft_Azure_LogicApps/LogicAppDesignerBlade/~/overview/id/${uriComponent(playbook.id)}'
