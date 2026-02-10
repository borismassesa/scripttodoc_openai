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

@description('API URL for the backend')
param apiUrl string

// Variables
var resourcePrefix = '${appName}-${environment}'
var frontendName = 'ca-${resourcePrefix}-frontend'

// Container App for Frontend
resource frontendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: frontendName
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
        targetPort: 3000
        transport: 'http'
        allowInsecure: false
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
          name: 'frontend'
          image: '${containerRegistryName}.azurecr.io/${appName}-frontend:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'NEXT_PUBLIC_API_URL'
              value: apiUrl
            }
            {
              name: 'NODE_ENV'
              value: 'production'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: 3000
              }
              initialDelaySeconds: 15
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: 3000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
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

// Output the Frontend URL
output frontendUrl string = 'https://${frontendContainerApp.properties.configuration.ingress.fqdn}'
output frontendPrincipalId string = frontendContainerApp.identity.principalId
