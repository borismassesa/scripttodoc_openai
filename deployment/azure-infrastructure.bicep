@description('Environment name (e.g., dev, staging, prod)')
param environment string = 'prod'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Application name')
param appName string = 'scripttodoc'

@description('GitHub repository URL (format: https://github.com/owner/repo)')
param githubRepoUrl string = ''

@description('GitHub branch name')
param githubBranch string = 'main'

// Variables
var resourcePrefix = '${appName}-${environment}'
var storageAccountName = replace('st${appName}${environment}', '-', '')

// ==================== Storage Account ====================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: take(storageAccountName, 24)
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    encryption: {
      services: {
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

resource uploadsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/uploads'
  properties: {
    publicAccess: 'None'
  }
}

resource documentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/documents'
  properties: {
    publicAccess: 'None'
  }
}

resource tempContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/temp'
  properties: {
    publicAccess: 'None'
  }
}

resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {
    policy: {
      rules: [
        {
          name: 'delete-temp-files'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: ['blockBlob']
              prefixMatch: ['temp/']
            }
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: 1
                }
              }
            }
          }
        }
        {
          name: 'delete-old-documents'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: ['blockBlob']
              prefixMatch: ['documents/', 'uploads/']
            }
            actions: {
              baseBlob: {
                delete: {
                  daysAfterModificationGreaterThan: 90
                }
              }
            }
          }
        }
      ]
    }
  }
}

// ==================== Cosmos DB ====================
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: 'cosmos-${resourcePrefix}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    minimalTlsVersion: 'Tls12'
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: appName
  properties: {
    resource: {
      id: appName
    }
  }
}

resource jobsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDatabase
  name: 'jobs'
  properties: {
    resource: {
      id: 'jobs'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: 7776000
    }
  }
}

// ==================== Service Bus ====================
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-${resourcePrefix}'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    minimumTlsVersion: '1.2'
  }
}

resource jobQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: '${appName}-jobs'
  properties: {
    maxDeliveryCount: 5
    defaultMessageTimeToLive: 'PT30M'
    deadLetteringOnMessageExpiration: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    requiresDuplicateDetection: true
  }
}

// ==================== Key Vault ====================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${resourcePrefix}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    enableRbacAuthorization: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ==================== Container Registry ====================
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: replace('cr${resourcePrefix}', '-', '')
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

// ==================== Log Analytics Workspace ====================
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${resourcePrefix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
  }
}

// ==================== Application Insights ====================
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-${resourcePrefix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    RetentionInDays: 90
  }
}

// ==================== Container Apps Environment ====================
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${resourcePrefix}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// ==================== Azure OpenAI ====================
resource openAIAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'openai-${resourcePrefix}'
  location: 'eastus'
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'openai-${resourcePrefix}'
    publicNetworkAccess: 'Enabled'
  }
}

resource openAIDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAIAccount
  name: 'gpt-4o-mini'
  sku: {
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
  }
}

// ==================== Document Intelligence ====================
resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: 'di-${resourcePrefix}'
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'di-${resourcePrefix}'
    publicNetworkAccess: 'Enabled'
  }
}

// ==================== Azure Static Web App ====================
// Only deploy if GitHub repository URL is provided
resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = if (githubRepoUrl != '') {
  name: 'swa-${resourcePrefix}'
  location: 'eastus2'
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    repositoryUrl: githubRepoUrl
    branch: githubBranch
    buildProperties: {
      appLocation: '/frontend'
      apiLocation: ''
      outputLocation: 'out'
    }
  }
}

// ==================== Outputs ====================
output resourceGroupName string = resourceGroup().name
output storageAccountName string = storageAccount.name
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosConnectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
output serviceBusConnectionString string = listKeys('${serviceBusNamespace.id}/AuthorizationRules/RootManageSharedAccessKey', serviceBusNamespace.apiVersion).primaryConnectionString
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerAppsEnvironmentId string = containerAppsEnvironment.id
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
output openAIEndpoint string = openAIAccount.properties.endpoint
output openAIKey string = openAIAccount.listKeys().key1
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output documentIntelligenceKey string = documentIntelligence.listKeys().key1
output staticWebAppName string = githubRepoUrl != '' ? staticWebApp.name : 'Not deployed - no GitHub URL provided'
output staticWebAppDefaultHostname string = githubRepoUrl != '' ? staticWebApp.properties.defaultHostname : 'Not deployed'
output staticWebAppUrl string = githubRepoUrl != '' ? 'https://${staticWebApp.properties.defaultHostname}' : 'Not deployed'
output staticWebAppDeploymentToken string = githubRepoUrl != '' ? staticWebApp.listSecrets().properties.apiKey : 'Not deployed'
