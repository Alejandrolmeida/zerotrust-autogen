// security.bicep - Security resources for Landing Zone
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
