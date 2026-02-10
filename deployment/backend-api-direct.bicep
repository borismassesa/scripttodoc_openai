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

@description('Docker image tag')
param imageTag string = 'latest'

// Secure parameters for secrets
@secure()
param azureOpenaiEndpoint string

@secure()
param azureOpenaiKey string

@secure()
param azureOpenaiDeployment string

@secure()
param azureDiEndpoint string

@secure()
param azureDiKey string

@secure()
param azureStorageAccountName string

@secure()
param azureStorageConnectionString string

@secure()
param azureCosmosEndpoint string

@secure()
param azureCosmosConnectionString string

@secure()
param azureServiceBusConnectionString string

@description('Use direct processing instead of Service Bus')
param useDirectProcessing string = 'true'

// Variables
var resourcePrefix = '${appName}-${environment}'
var apiName = 'ca-${resourcePrefix}-api'

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
          allowedOrigins: ['https://ca-scripttodoc-prod-frontend.delightfuldune-05b8c4e7.eastus.azurecontainerapps.io']
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
          value: azureOpenaiEndpoint
        }
        {
          name: 'azure-openai-key'
          value: azureOpenaiKey
        }
        {
          name: 'azure-openai-deployment'
          value: azureOpenaiDeployment
        }
        {
          name: 'azure-di-endpoint'
          value: azureDiEndpoint
        }
        {
          name: 'azure-di-key'
          value: azureDiKey
        }
        {
          name: 'azure-storage-account-name'
          value: azureStorageAccountName
        }
        {
          name: 'azure-storage-connection-string'
          value: azureStorageConnectionString
        }
        {
          name: 'azure-cosmos-endpoint'
          value: azureCosmosEndpoint
        }
        {
          name: 'azure-cosmos-connection-string'
          value: azureCosmosConnectionString
        }
        {
          name: 'azure-service-bus-connection-string'
          value: azureServiceBusConnectionString
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
            {
              name: 'USE_DIRECT_PROCESSING'
              value: useDirectProcessing
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
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '50'
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
