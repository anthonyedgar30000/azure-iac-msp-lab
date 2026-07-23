targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param tags object
param virtualNetworkId string
param loadBalancerName string
param operationsNsgName string
param collectorVmName string
param collectorPrivateIpAddress string
param dnsLabel string
param allowedOrigin string
param backendTransactionUrl string
param sourceRepository string
param sourceRef string
param installerUri string

var resourceSuffix = '${prefix}-${environment}'
var frontendName = 'fe-public-st-demo-api'
var backendPoolName = 'be-st-demo-api'
var probeName = 'probe-tcp-443-st-demo-api'

resource publicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: 'pip-st-demo-api-${resourceSuffix}'
  location: location
  sku: {
    name: 'Standard'
  }
  tags: union(tags, {
    component: 'collector-hosted-demo-api'
    exposure: 'load-balanced-public-https'
  })
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
    dnsSettings: {
      domainNameLabel: dnsLabel
    }
  }
}

resource loadBalancer 'Microsoft.Network/loadBalancers@2024-05-01' existing = {
  name: loadBalancerName
}

resource apiFrontend 'Microsoft.Network/loadBalancers/frontendIPConfigurations@2024-05-01' = {
  parent: loadBalancer
  name: frontendName
  properties: {
    publicIPAddress: {
      id: publicIp.id
    }
  }
}

resource apiBackendPool 'Microsoft.Network/loadBalancers/backendAddressPools@2024-05-01' = {
  parent: loadBalancer
  name: backendPoolName
  properties: {
    virtualNetwork: {
      id: virtualNetworkId
    }
    loadBalancerBackendAddresses: [
      {
        name: 'collector'
        properties: {
          ipAddress: collectorPrivateIpAddress
          virtualNetwork: {
            id: virtualNetworkId
          }
        }
      }
    ]
  }
}

resource apiProbe 'Microsoft.Network/loadBalancers/probes@2024-05-01' = {
  parent: loadBalancer
  name: probeName
  properties: {
    protocol: 'Tcp'
    port: 443
    intervalInSeconds: 5
    numberOfProbes: 2
  }
}

resource apiHttpRule 'Microsoft.Network/loadBalancers/loadBalancingRules@2024-05-01' = {
  parent: loadBalancer
  name: 'rule-st-demo-api-http'
  properties: {
    frontendIPConfiguration: {
      id: apiFrontend.id
    }
    backendAddressPool: {
      id: apiBackendPool.id
    }
    probe: {
      id: apiProbe.id
    }
    protocol: 'Tcp'
    frontendPort: 80
    backendPort: 80
    enableFloatingIP: false
    idleTimeoutInMinutes: 4
    loadDistribution: 'Default'
    disableOutboundSnat: true
    enableTcpReset: true
  }
}

resource apiHttpsRule 'Microsoft.Network/loadBalancers/loadBalancingRules@2024-05-01' = {
  parent: loadBalancer
  name: 'rule-st-demo-api-https'
  properties: {
    frontendIPConfiguration: {
      id: apiFrontend.id
    }
    backendAddressPool: {
      id: apiBackendPool.id
    }
    probe: {
      id: apiProbe.id
    }
    protocol: 'Tcp'
    frontendPort: 443
    backendPort: 443
    enableFloatingIP: false
    idleTimeoutInMinutes: 4
    loadDistribution: 'Default'
    disableOutboundSnat: true
    enableTcpReset: true
  }
}

resource operationsNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' existing = {
  name: operationsNsgName
}

resource allowDemoApiHttp 'Microsoft.Network/networkSecurityGroups/securityRules@2024-05-01' = {
  parent: operationsNsg
  name: 'Allow-Demo-API-HTTP-From-Internet'
  properties: {
    priority: 140
    access: 'Allow'
    direction: 'Inbound'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '80'
    sourceAddressPrefix: 'Internet'
    destinationAddressPrefix: collectorPrivateIpAddress
  }
}

resource allowDemoApiHttps 'Microsoft.Network/networkSecurityGroups/securityRules@2024-05-01' = {
  parent: operationsNsg
  name: 'Allow-Demo-API-HTTPS-From-Internet'
  properties: {
    priority: 150
    access: 'Allow'
    direction: 'Inbound'
    protocol: 'Tcp'
    sourcePortRange: '*'
    destinationPortRange: '443'
    sourceAddressPrefix: 'Internet'
    destinationAddressPrefix: collectorPrivateIpAddress
  }
}

resource collectorVm 'Microsoft.Compute/virtualMachines@2024-07-01' existing = {
  name: collectorVmName
}

resource demoApiExtension 'Microsoft.Compute/virtualMachines/extensions@2024-07-01' = {
  parent: collectorVm
  name: 'servicetracer-demo-api'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Extensions'
    type: 'CustomScript'
    typeHandlerVersion: '2.1'
    autoUpgradeMinorVersion: true
    protectedSettings: {
      fileUris: [
        installerUri
      ]
      commandToExecute: 'bash install_collector_demo_api.sh ${sourceRepository} ${sourceRef} ${publicIp.properties.dnsSettings.fqdn} ${backendTransactionUrl} ${allowedOrigin}'
    }
  }
  dependsOn: [
    apiHttpRule
    apiHttpsRule
    allowDemoApiHttp
    allowDemoApiHttps
  ]
}

output publicIpId string = publicIp.id
output fqdn string = publicIp.properties.dnsSettings.fqdn
output healthUrl string = 'https://${publicIp.properties.dnsSettings.fqdn}/api/health'
output runUrl string = 'https://${publicIp.properties.dnsSettings.fqdn}/api/demo/run'
output collectorRemainsPrivate bool = true
