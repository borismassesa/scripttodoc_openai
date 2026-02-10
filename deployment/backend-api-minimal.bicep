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

// Variables
var resourcePrefix = '${appName}-${environment}'
var apiName = 'ca-${resourcePrefix}-api'

// Container App for API - MINIMAL VERSION (no Key Vault references)
// This creates the identity first, then we'll update it with Key Vault references via CLI
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
          allowedOrigins: ['*']
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
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${containerRegistryName}.azurecr.io/${appName}-api:${imageTag}'
          env: [
            {
              name: 'PORT'
              value: '8000'
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output apiUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'
output apiPrincipalId string = apiContainerApp.identity.principalId
