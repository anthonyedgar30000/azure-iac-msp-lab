targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param virtualNetworkAddressPrefix string
param remoteUserVirtualNetworkAddressPrefix string
param vpnClientAddressPrefix string
param tags object

var resourceSuffix = '${prefix}-${environment}'
var subnetPrefixes = {
  edge: '10.20.10.0/24'
  identity: '10.20.20.0/24'
  servers: '10.20.30.0/24'
  operations: '10.20.40.0/24'
  remoteUsers: '10.30.10.0/24'
}

resource edgeNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-edge-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'edge-network' })
  properties: {
    securityRules: [
      {
        name: 'Allow-HTTPS-From-Internet'
        properties: {
          priority: 100
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'Internet'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-Azure-Load-Balancer'
        properties: {
          priority: 110
          access: 'Allow'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'AzureLoadBalancer'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-Management-From-Operations'
        properties: {
          priority: 120
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '22'
            '443'
          ]
          sourceAddressPrefix: subnetPrefixes.operations
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Deny-Other-VNet-Inbound'
        properties: {
          priority: 4000
          access: 'Deny'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource identityNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-identity-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'identity-network' })
  properties: {
    securityRules: [
      {
        name: 'Allow-RADIUS-From-Edge'
        properties: {
          priority: 100
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Udp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '1812'
            '1813'
          ]
          sourceAddressPrefix: subnetPrefixes.edge
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-DNS-From-VPN-Clients-UDP'
        properties: {
          priority: 105
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Udp'
          sourcePortRange: '*'
          destinationPortRange: '53'
          sourceAddressPrefix: vpnClientAddressPrefix
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-DNS-From-VPN-Clients-TCP'
        properties: {
          priority: 106
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '53'
          sourceAddressPrefix: vpnClientAddressPrefix
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-DNS-From-VNet-UDP'
        properties: {
          priority: 110
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Udp'
          sourcePortRange: '*'
          destinationPortRange: '53'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-DNS-From-VNet-TCP'
        properties: {
          priority: 120
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '53'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-AD-Core-From-VPN-Clients'
        properties: {
          priority: 125
          access: 'Allow'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRanges: [
            '88'
            '123'
            '135'
            '389'
            '445'
            '464'
            '636'
            '3268'
            '3269'
            '49152-65535'
          ]
          sourceAddressPrefix: vpnClientAddressPrefix
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-AD-Core-From-VNet'
        properties: {
          priority: 130
          access: 'Allow'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRanges: [
            '88'
            '123'
            '135'
            '389'
            '445'
            '464'
            '636'
            '3268'
            '3269'
            '49152-65535'
          ]
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-Management-From-Operations'
        properties: {
          priority: 140
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '3389'
            '5985'
            '5986'
          ]
          sourceAddressPrefix: subnetPrefixes.operations
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Deny-Other-VNet-Inbound'
        properties: {
          priority: 4000
          access: 'Deny'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource serversNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-servers-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'server-network' })
  properties: {
    securityRules: [
      {
        name: 'Allow-RDP-From-Remote-Users'
        properties: {
          priority: 100
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '3389'
          sourceAddressPrefix: vpnClientAddressPrefix
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-Management-From-Operations'
        properties: {
          priority: 110
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '3389'
            '5985'
            '5986'
          ]
          sourceAddressPrefix: subnetPrefixes.operations
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Deny-Other-VNet-Inbound'
        properties: {
          priority: 4000
          access: 'Deny'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource operationsNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-operations-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'operations-network' })
  properties: {
    securityRules: [
      {
        name: 'Allow-Syslog-From-VNet-TCP'
        properties: {
          priority: 100
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '514'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-Syslog-From-VNet-UDP'
        properties: {
          priority: 110
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Udp'
          sourcePortRange: '*'
          destinationPortRange: '514'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-SNMP-Traps-From-Edge'
        properties: {
          priority: 120
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Udp'
          sourcePortRange: '*'
          destinationPortRange: '162'
          sourceAddressPrefix: subnetPrefixes.edge
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-ServiceTracer-From-VNet'
        properties: {
          priority: 130
          access: 'Allow'
          direction: 'Inbound'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '8080'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Deny-Other-VNet-Inbound'
        properties: {
          priority: 4000
          access: 'Deny'
          direction: 'Inbound'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource remoteUsersNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-remote-users-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'remote-user-network' })
  properties: {
    securityRules: []
  }
}

resource onPremVirtualNetwork 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'vnet-onprem-sim-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'network' })
  properties: {
    addressSpace: {
      addressPrefixes: [
        virtualNetworkAddressPrefix
      ]
    }
  }
}

resource remoteUserVirtualNetwork 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'vnet-remote-users-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'remote-user-network' })
  properties: {
    addressSpace: {
      addressPrefixes: [
        remoteUserVirtualNetworkAddressPrefix
      ]
    }
  }
}

resource edgeSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' = {
  parent: onPremVirtualNetwork
  name: 'snet-edge'
  properties: {
    addressPrefix: subnetPrefixes.edge
    networkSecurityGroup: {
      id: edgeNsg.id
    }
  }
}

resource identitySubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' = {
  parent: onPremVirtualNetwork
  name: 'snet-identity'
  properties: {
    addressPrefix: subnetPrefixes.identity
    networkSecurityGroup: {
      id: identityNsg.id
    }
  }
}

resource serversSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' = {
  parent: onPremVirtualNetwork
  name: 'snet-servers'
  properties: {
    addressPrefix: subnetPrefixes.servers
    networkSecurityGroup: {
      id: serversNsg.id
    }
  }
}

resource operationsSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' = {
  parent: onPremVirtualNetwork
  name: 'snet-operations'
  properties: {
    addressPrefix: subnetPrefixes.operations
    networkSecurityGroup: {
      id: operationsNsg.id
    }
  }
}

resource remoteUsersSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' = {
  parent: remoteUserVirtualNetwork
  name: 'snet-remote-users'
  properties: {
    addressPrefix: subnetPrefixes.remoteUsers
    networkSecurityGroup: {
      id: remoteUsersNsg.id
    }
  }
}

output onPremVirtualNetworkId string = onPremVirtualNetwork.id
output remoteUserVirtualNetworkId string = remoteUserVirtualNetwork.id
output subnetIds object = {
  edge: edgeSubnet.id
  identity: identitySubnet.id
  servers: serversSubnet.id
  operations: operationsSubnet.id
  remoteUsers: remoteUsersSubnet.id
}
