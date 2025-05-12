// governance.bicep - Governance resources for Landing Zone
// Generated automatically for Zero-Trust project

param location string
param organizationName string
param environmentName string
param resourceToken string
param tags object

// Resource Groups variables
var resourceGroups = [
  {
    name: 'rg-${organizationName}-${environmentName}-network'
    location: location
    tags: union(tags, {
      layer: 'networking'
    })
  }
  {
    name: 'rg-${organizationName}-${environmentName}-security'
    location: location
    tags: union(tags, {
      layer: 'security'
    })
  }
  {
    name: 'rg-${organizationName}-${environmentName}-mgmt'
    location: location
    tags: union(tags, {
      layer: 'management'
    })
  }
]

// Policy Assignment
resource policyAssignment 'Microsoft.Authorization/policyAssignments@2020-09-01' = {
  name: 'pa-${resourceToken}'
  location: location
  properties: {
    displayName: 'Landing Zone Security Standards'
    policyDefinitionId: '/providers/Microsoft.Authorization/policyDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8' // Azure Security Benchmark
    parameters: {}
  }
}

// Resource Groups - Skip creation at module level, should be created separately
output resourceGroupNames array = [for rg in resourceGroups: rg.name]

// Outputs
output policyAssignmentId string = policyAssignment.id
