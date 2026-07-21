targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param edgeSubnetId string
param loadBalancerBackendPoolId string
param tags object

@description('Linux administrator account used for controlled recovery operations.')
param adminUsername string

@secure()
@description('SSH public key for the demo backend administrator account.')
param adminSshPublicKey string

@description('Azure VM size used by each simulated VPN backend.')
param vmSize string = 'Standard_B1s'

@description('HTTPS listener port shared by the load-balancer rule and both backends.')
@minValue(1)
@maxValue(65535)
param listenerPort int = 443

var resourceSuffix = '${prefix}-${environment}'
var bootstrapTemplate = loadTextContent('../bootstrap/vpn-backend-cloud-init.yaml')
var backends = [
  {
    key: 'vpn01'
    backendId: 'VPN-01'
    computerName: 'vpn01-${environment}'
    privateIpAddress: '10.20.10.11'
    mode: 'healthy'
  }
  {
    key: 'vpn02'
    backendId: 'VPN-02'
    computerName: 'vpn02-${environment}'
    privateIpAddress: '10.20.10.12'
    mode: 'radius-timeout'
  }
]

resource availabilitySet 'Microsoft.Compute/availabilitySets@2024-03-01' = {
  name: 'avset-vpn-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'remote-access-backends' })
  sku: {
    name: 'Aligned'
  }
  properties: {
    platformFaultDomainCount: 2
    platformUpdateDomainCount: 5
  }
}

resource backendNics 'Microsoft.Network/networkInterfaces@2024-05-01' = [for backend in backends: {
  name: 'nic-${backend.key}-${resourceSuffix}'
  location: location
  tags: union(tags, {
    component: 'remote-access-backend'
    backend: backend.backendId
  })
  properties: {
    enableAcceleratedNetworking: false
    ipConfigurations: [
      {
        name: 'ipconfig-primary'
        properties: {
          privateIPAllocationMethod: 'Static'
          privateIPAddress: backend.privateIpAddress
          primary: true
          subnet: {
            id: edgeSubnetId
          }
          loadBalancerBackendAddressPools: [
            {
              id: loadBalancerBackendPoolId
            }
          ]
        }
      }
    ]
  }
}]

resource backendVms 'Microsoft.Compute/virtualMachines@2024-07-01' = [for (backend, index) in backends: {
  name: 'vm-${backend.key}-${resourceSuffix}'
  location: location
  tags: union(tags, {
    component: 'remote-access-backend'
    backend: backend.backendId
    demoMode: backend.mode
  })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    availabilitySet: {
      id: availabilitySet.id
    }
    hardwareProfile: {
      vmSize: vmSize
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: 'ubuntu-24_04-lts'
        sku: 'server'
        version: 'latest'
      }
      osDisk: {
        name: 'disk-${backend.key}-os-${resourceSuffix}'
        createOption: 'FromImage'
        deleteOption: 'Delete'
        caching: 'ReadWrite'
        managedDisk: {
          storageAccountType: 'StandardSSD_LRS'
        }
      }
    }
    osProfile: {
      computerName: backend.computerName
      adminUsername: adminUsername
      customData: base64(
        replace(
          replace(
            replace(bootstrapTemplate, '__BACKEND_ID__', backend.backendId),
            '__BACKEND_MODE__',
            backend.mode
          ),
          '__LISTENER_PORT__',
          string(listenerPort)
        )
      )
      linuxConfiguration: {
        disablePasswordAuthentication: true
        provisionVMAgent: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: adminSshPublicKey
            }
          ]
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: backendNics[index].id
          properties: {
            primary: true
            deleteOption: 'Delete'
          }
        }
      ]
    }
    securityProfile: {
      securityType: 'TrustedLaunch'
      uefiSettings: {
        secureBootEnabled: true
        vTpmEnabled: true
      }
    }
    diagnosticsProfile: {
      bootDiagnostics: {
        enabled: true
      }
    }
  }
}]

output backendVmIds array = [for (backend, index) in backends: {
  backendId: backend.backendId
  vmId: backendVms[index].id
  vmName: backendVms[index].name
  nicId: backendNics[index].id
  privateIpAddress: backend.privateIpAddress
  mode: backend.mode
}]

output backendPrivateIpAddresses object = {
  vpn01: backends[0].privateIpAddress
  vpn02: backends[1].privateIpAddress
}
