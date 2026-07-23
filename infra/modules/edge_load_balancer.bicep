targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param tags object

@description('Public listener port used by the remote-access demo.')
@minValue(1)
@maxValue(65535)
param listenerPort int = 443

var resourceSuffix = '${prefix}-${environment}'
var loadBalancerName = 'lb-remote-access-${resourceSuffix}'
var frontendName = 'fe-public-remote-access'
var backendPoolName = 'be-vpn-gateways'
var probeName = 'probe-tcp-${listenerPort}-shallow'
var ruleName = 'rule-remote-access-${listenerPort}'

resource publicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: 'pip-remote-access-${resourceSuffix}'
  location: location
  sku: {
    name: 'Standard'
  }
  tags: union(tags, { component: 'remote-access-ingress' })
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
  }
}

resource loadBalancer 'Microsoft.Network/loadBalancers@2024-05-01' = {
  name: loadBalancerName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Regional'
  }
  tags: union(tags, { component: 'remote-access-load-balancer' })
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
      }
    ]
    probes: [
      {
        name: probeName
        properties: {
          protocol: 'Tcp'
          port: listenerPort
          intervalInSeconds: 5
          numberOfProbes: 2
        }
      }
    ]
    loadBalancingRules: [
      {
        name: ruleName
        properties: {
          frontendIPConfiguration: {
            id: resourceId(
              'Microsoft.Network/loadBalancers/frontendIPConfigurations',
              loadBalancerName,
              frontendName
            )
          }
          backendAddressPool: {
            id: resourceId(
              'Microsoft.Network/loadBalancers/backendAddressPools',
              loadBalancerName,
              backendPoolName
            )
          }
          probe: {
            id: resourceId(
              'Microsoft.Network/loadBalancers/probes',
              loadBalancerName,
              probeName
            )
          }
          protocol: 'Tcp'
          frontendPort: listenerPort
          backendPort: listenerPort
          enableFloatingIP: false
          idleTimeoutInMinutes: 4
          loadDistribution: 'Default'
          disableOutboundSnat: true
        }
      }
    ]
  }
}

output loadBalancerId string = loadBalancer.id
output publicIpAddressId string = publicIp.id
output publicIpAddress string = publicIp.properties.ipAddress
output backendPoolId string = resourceId(
  'Microsoft.Network/loadBalancers/backendAddressPools',
  loadBalancerName,
  backendPoolName
)
output healthProbe object = {
  name: probeName
  protocol: 'Tcp'
  port: listenerPort
  scope: 'listener-only'
}
