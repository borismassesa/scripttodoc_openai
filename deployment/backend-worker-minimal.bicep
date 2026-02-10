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

// Variables
var resourcePrefix = '${appName}-${environment}'
// Short name keeps the Container App within the 32-character limit
var workerName = 'ca-${resourcePrefix}-wrk'

// Container App for Worker - MINIMAL VERSION (no Key Vault references)
// This creates the identity first, then we'll update it with Key Vault references
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
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        // Note: Service Bus scaling rule will be added in the full deployment
        // after the identity has permissions
      }
    }
  }
}

// Output the worker principal ID
output workerPrincipalId string = workerContainerApp.identity.principalId
