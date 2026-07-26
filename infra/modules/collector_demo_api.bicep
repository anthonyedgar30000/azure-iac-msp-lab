targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param tags object
param virtualNetworkId string
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
var publicIpName = 'pip-st-demo-api-${resourceSuffix}'
var loadBalancerName = 'lb-st-demo-api-${resourceSuffix}'
var frontendName = 'fe-public-st-demo-api'
var backendPoolName = 'be-st-demo-api'
var probeName = 'probe-tcp-80-st-demo-api'
var httpRuleName = 'rule-st-demo-api-http'
var httpsRuleName = 'rule-st-demo-api-https'

resource publicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: publicIpName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Regional'
  }
  tags: union(tags, {
    component: 'collector-hosted-demo-api'
    exposure: 'dedicated-load-balanced-public-https'
  })
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
    ddosSettings: {
      protectionMode: 'VirtualNetworkInherited'
    }
    dnsSettings: {
      domainNameLabel: dnsLabel
    }
  }
}

// Keep the demo API ingress isolated from the existing remote-access load balancer.
// Frontend, probe, and rules remain on the atomic parent PUT. The IP backend pool is
// created as an empty placeholder here, then converged through its supported child API.
resource demoApiLoadBalancer 'Microsoft.Network/loadBalancers@2024-05-01' = {
  name: loadBalancerName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Regional'
  }
  tags: union(tags, {
    component: 'collector-hosted-demo-api-load-balancer'
    exposure: 'public-https'
  })
  properties: {
    frontendIPConfigurations: [
      {
        name: frontendName
        properties: {
          publicIPAddress: {
            id: publicIp.id
          }
        }
      }
    ]
    backendAddressPools: [
      {
        name: backendPoolName
        properties: {}
      }
    ]
    probes: [
      {
        name: probeName
        properties: {
          protocol: 'Tcp'
          port: 80
          intervalInSeconds: 5
          numberOfProbes: 2
        }
      }
    ]
    loadBalancingRules: [
      {
        name: httpRuleName
        properties: {
          frontendIPConfiguration: {
            id: resourceId('Microsoft.Network/loadBalancers/frontendIPConfigurations', loadBalancerName, frontendName)
          }
          backendAddressPool: {
            id: resourceId('Microsoft.Network/loadBalancers/backendAddressPools', loadBalancerName, backendPoolName)
          }
          probe: {
            id: resourceId('Microsoft.Network/loadBalancers/probes', loadBalancerName, probeName)
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
      {
        name: httpsRuleName
        properties: {
          frontendIPConfiguration: {
            id: resourceId('Microsoft.Network/loadBalancers/frontendIPConfigurations', loadBalancerName, frontendName)
          }
          backendAddressPool: {
            id: resourceId('Microsoft.Network/loadBalancers/backendAddressPools', loadBalancerName, backendPoolName)
          }
          probe: {
            id: resourceId('Microsoft.Network/loadBalancers/probes', loadBalancerName, probeName)
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
    ]
  }
}

// Azure retained the dedicated pool but dropped the inline IP address during the observed
// deployment. Converge the address explicitly through the backend-pool child resource.
resource demoApiBackendPool 'Microsoft.Network/loadBalancers/backendAddressPools@2024-05-01' = {
  parent: demoApiLoadBalancer
  name: backendPoolName
  properties: {
    loadBalancerBackendAddresses: [
      {
        name: 'collector'
        properties: {
          ipAddress: collectorPrivateIpAddress
          // IP-based pools must set the virtual network at either pool or address level,
          // never both. Use the address level for this single proven target.
          virtualNetwork: {
            id: virtualNetworkId
          }
        }
      }
    ]
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
    // The extension already exists in a terminal failed state. Bind each retry to the
    // exact reviewed source commit so a new authorized deployment deterministically reruns it.
    forceUpdateTag: sourceRef
    protectedSettings: {
      fileUris: [
        installerUri
      ]
      commandToExecute: 'bash install_collector_demo_api.sh ${sourceRepository} ${sourceRef} ${publicIp.properties.dnsSettings.fqdn} ${backendTransactionUrl} ${allowedOrigin}'
    }
  }
  dependsOn: [
    demoApiBackendPool
    allowDemoApiHttp
    allowDemoApiHttps
  ]
}

output publicIpId string = publicIp.id
output loadBalancerId string = demoApiLoadBalancer.id
output fqdn string = publicIp.properties.dnsSettings.fqdn
output healthUrl string = 'https://${publicIp.properties.dnsSettings.fqdn}/api/health'
output runUrl string = 'https://${publicIp.properties.dnsSettings.fqdn}/api/demo/run'
output collectorRemainsPrivate bool = true
