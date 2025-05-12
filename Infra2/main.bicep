// main.bicep - Landing Zone for GlobalAzure (prod)
// Generated automatically for Zero-Trust project

targetScope = 'resourceGroup'

// Parameters
@description('Name of the organization')
param organizationName string = 'GlobalAzure'

@description('Deployment environment name')
@allowed([
  'dev'
  'test'
  'prod'
])
param environmentName string = 'prod'

@description('Primary Azure region for resource deployment')
param location string = resourceGroup().location

@description('Tagging object for resource tagging')
param tags object = {
  environment: environmentName
  applicationName: 'LandingZone'
  organizationName: organizationName
  createdBy: 'ZeroTrustAutomation'
}

// Variables
var resourceToken = toLower(uniqueString(subscription().id, environmentName, organizationName))

// Resource Group tagging
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' existing = {
  name: resourceGroup().name
}

resource rgTags 'Microsoft.Resources/tags@2021-04-01' = {
  name: 'default'
  scope: rg
  properties: {
    tags: tags
  }
}

// Modules
module networking 'modules/networking.bicep' = {
  name: 'networking-deployment'
  params: {
    location: location
    environmentName: environmentName
    organizationName: organizationName
    resourceToken: resourceToken
    tags: tags
  }
}

module security 'modules/security.bicep' = {
  name: 'security-deployment'
  params: {
    location: location
    environmentName: environmentName
    organizationName: organizationName
    resourceToken: resourceToken
    tags: tags
  }
}

module governance 'modules/governance.bicep' = {
  name: 'governance-deployment'
  params: {
    location: location
    environmentName: environmentName
    organizationName: organizationName
    resourceToken: resourceToken
    tags: tags
  }
}

// Outputs
output resourceGroupId string = resourceGroup().id
output deploymentName string = deployment().name
output vnetId string = networking.outputs.vnetId
