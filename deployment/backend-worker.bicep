@description('Environment name')
param environment string

@description('Location for resources')
param location string = resourceGroup().location

@description('Application name')
param appName string

@description('Container registry name')
param containerRegistryName string

@description('Container Apps Environment ID')
param containerAppsEnvironmentId string

@description('Key Vault name')
param keyVaultName string

@description('Service Bus namespace name')
param serviceBusNamespaceName string

@description('Docker image tag')
param imageTag string = 'latest'

// Variables
var resourcePrefix = '${appName}-${environment}'
// Short name keeps the Container App within the 32-character limit
var workerName = 'ca-${resourcePrefix}-wrk'

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Container App for Worker
resource workerContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: workerName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          username: containerRegistryName
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: listCredentials(resourceId('Microsoft.ContainerRegistry/registries', containerRegistryName), '2023-07-01').passwords[0].value
        }
        {
          name: 'azure-openai-endpoint'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-openai-endpoint'
          identity: 'system'
        }
        {
          name: 'azure-openai-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-openai-key'
          identity: 'system'
        }
        {
          name: 'azure-openai-deployment'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-openai-deployment'
          identity: 'system'
        }
        {
          name: 'azure-di-endpoint'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-di-endpoint'
          identity: 'system'
        }
        {
          name: 'azure-di-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-di-key'
          identity: 'system'
        }
        {
          name: 'azure-storage-account-name'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-storage-account-name'
          identity: 'system'
        }
        {
          name: 'azure-storage-connection-string'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-storage-connection-string'
          identity: 'system'
        }
        {
          name: 'azure-cosmos-endpoint'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-cosmos-endpoint'
          identity: 'system'
        }
        {
          name: 'azure-cosmos-connection-string'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-cosmos-connection-string'
          identity: 'system'
        }
        {
          name: 'azure-service-bus-connection-string'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/azure-service-bus-connection-string'
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${containerRegistryName}.azurecr.io/${appName}-worker:${imageTag}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'PYTHON_ENV'
              value: 'production'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              secretRef: 'azure-openai-endpoint'
            }
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              secretRef: 'azure-openai-deployment'
            }
            {
              name: 'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'
              secretRef: 'azure-di-endpoint'
            }
            {
              name: 'AZURE_DOCUMENT_INTELLIGENCE_KEY'
              secretRef: 'azure-di-key'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              secretRef: 'azure-storage-account-name'
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'azure-storage-connection-string'
            }
            {
              name: 'AZURE_COSMOS_ENDPOINT'
              secretRef: 'azure-cosmos-endpoint'
            }
            {
              name: 'AZURE_COSMOS_CONNECTION_STRING'
              secretRef: 'azure-cosmos-connection-string'
            }
            {
              name: 'AZURE_SERVICE_BUS_CONNECTION_STRING'
              secretRef: 'azure-service-bus-connection-string'
            }
          ]
        }
      ]
      scale: {
        // COST OPTIMIZATION: Scale to zero when idle (saves 70-85% on compute costs)
        // Worker will scale up automatically when messages arrive in Service Bus queue
        // Change to minReplicas: 1 if you need always-on processing (no cold starts)
        minReplicas: 0
        maxReplicas: 5
        rules: [
          {
            name: 'queue-scaling'
            custom: {
              type: 'azure-servicebus'
              metadata: {
                queueName: '${appName}-jobs'
                // Scale up when 5+ messages in queue
                messageCount: '5'
                namespace: serviceBusNamespaceName
              }
              identity: 'system'
            }
          }
        ]
      }
    }
  }
}

// Output the worker principal ID
output workerPrincipalId string = workerContainerApp.identity.principalId
