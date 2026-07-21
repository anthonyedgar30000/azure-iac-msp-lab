targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param operationsSubnetId string
param tags object

@description('Private IPv4 address assigned to the collector NIC.')
param privateIpAddress string

@description('Linux administrator account used for controlled management and recovery.')
param adminUsername string

@secure()
@description('SSH public key for the Linux administrator account. Required when the collector VM is deployed.')
param adminSshPublicKey string

@description('Azure VM size for the collector.')
param vmSize string

@description('Size of the separately managed evidence disk in GiB.')
@minValue(16)
param dataDiskSizeGb int

@description('HTTPS port exposed by the ServiceTracer collector inside the operations network.')
@minValue(1)
@maxValue(65535)
param collectorPort int

@description('Public Git repository containing the ServiceTracer package.')
param collectorSourceRepository string

@description('Branch, tag, or commit fetched during bootstrap. Pin a commit for repeatable deployments.')
param collectorSourceRef string

var resourceSuffix = '${prefix}-${environment}'
var collectorName = 'vm-stcollector-${resourceSuffix}'
var collectorComputerName = 'stcollector-${environment}'
var bootstrapTemplate = loadTextContent('../bootstrap/collector-cloud-init.yaml')
var bootstrapWithRepository = replace(bootstrapTemplate, '__COLLECTOR_SOURCE_REPOSITORY__', collectorSourceRepository)
var bootstrapWithRef = replace(bootstrapWithRepository, '__COLLECTOR_SOURCE_REF__', collectorSourceRef)
var bootstrapWithPort = replace(bootstrapWithRef, '__COLLECTOR_PORT__', string(collectorPort))
var bootstrapWithPrivateIp = replace(bootstrapWithPort, '__COLLECTOR_PRIVATE_IP__', privateIpAddress)
var renderedBootstrap = replace(bootstrapWithPrivateIp, '__COLLECTOR_CERTIFICATE_NAME__', collectorComputerName)

resource collectorNic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: 'nic-stcollector-${resourceSuffix}'
  location: location
  tags: union(tags, { component: 'servicetracer-collector' })
  properties: {
    enableAcceleratedNetworking: false
    ipConfigurations: [
      {
        name: 'ipconfig-primary'
        properties: {
          privateIPAllocationMethod: 'Static'
          privateIPAddress: privateIpAddress
          primary: true
          subnet: {
            id: operationsSubnetId
          }
        }
      }
    ]
  }
}

resource evidenceDisk 'Microsoft.Compute/disks@2024-03-02' = {
  name: 'disk-stcollector-evidence-${resourceSuffix}'
  location: location
  tags: union(tags, {
    component: 'servicetracer-evidence'
    dataClassification: 'operational-evidence'
  })
  sku: {
    name: 'StandardSSD_LRS'
  }
  properties: {
    diskSizeGB: dataDiskSizeGb
    creationData: {
      createOption: 'Empty'
    }
    networkAccessPolicy: 'DenyAll'
    publicNetworkAccess: 'Disabled'
  }
}

resource collectorVm 'Microsoft.Compute/virtualMachines@2024-07-01' = {
  name: collectorName
  location: location
  tags: union(tags, { component: 'servicetracer-collector' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
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
        name: 'disk-stcollector-os-${resourceSuffix}'
        createOption: 'FromImage'
        deleteOption: 'Delete'
        caching: 'ReadWrite'
        managedDisk: {
          storageAccountType: 'StandardSSD_LRS'
        }
      }
      dataDisks: [
        {
          name: evidenceDisk.name
          lun: 0
          createOption: 'Attach'
          deleteOption: 'Detach'
          caching: 'None'
          managedDisk: {
            id: evidenceDisk.id
            storageAccountType: 'StandardSSD_LRS'
          }
        }
      ]
    }
    osProfile: {
      computerName: collectorComputerName
      adminUsername: adminUsername
      customData: base64(renderedBootstrap)
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
          id: collectorNic.id
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
}

output collectorVmId string = collectorVm.id
output collectorPrincipalId string = collectorVm.identity.principalId
output collectorNicId string = collectorNic.id
output collectorPrivateIpAddress string = privateIpAddress
output collectorEndpoint string = 'https://${privateIpAddress}:${collectorPort}'
output evidenceDiskId string = evidenceDisk.id
output collectorSource object = {
  repository: collectorSourceRepository
  reference: collectorSourceRef
}
