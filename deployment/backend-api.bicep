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

@description('Docker image tag')
param imageTag string = 'latest'

// Variables
var resourcePrefix = '${appName}-${environment}'
var apiName = 'ca-${resourcePrefix}-api'

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Container App for API
resource apiContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: apiName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: ['*']  // Will be updated with Static Web App URL
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          exposeHeaders: ['*']
          maxAge: 3600
          allowCredentials: true
        }
      }
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
          name: 'api'
          image: '${containerRegistryName}.azurecr.io/${appName}-api:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
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
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 15
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        // COST OPTIMIZATION: Scale to zero when idle (saves 70-85% on compute costs)
        // Change to minReplicas: 1 if you need always-on availability (no cold starts)
        minReplicas: 0
        maxReplicas: 10
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                // Scale up when 10+ concurrent requests (more aggressive than default 50)
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Output the API URL
output apiUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'
output apiPrincipalId string = apiContainerApp.identity.principalId
