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

@description('Service Bus namespace name')
param serviceBusNamespaceName string

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

// Variables
var resourcePrefix = '${appName}-${environment}'
// Short name keeps the Container App within the 32-character limit
var workerName = 'ca-${resourcePrefix}-wrk'

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
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'queue-scaling'
            custom: {
              type: 'azure-servicebus'
              metadata: {
                queueName: '${appName}-jobs'
                messageCount: '5'
                namespace: serviceBusNamespaceName
              }
            }
          }
        ]
      }
    }
  }
}

// Output the worker principal ID
output workerPrincipalId string = workerContainerApp.identity.principalId
