targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param operationsSubnetId string
param operationsNsgName string
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

@description('Expose the bounded demo API through Nginx on this existing collector VM.')
param deployCollectorDemoApi bool = false

@description('Globally unique DNS label for the collector-hosted demo API public IP.')
param demoApiDnsLabel string = ''

@description('Exact GitHub Pages origin allowed by the demo API CORS policy.')
param demoApiAllowedOrigin string = 'https://anthonyedgar30000.github.io'

@description('Fixed synthetic backend transaction endpoint called by the demo API.')
param demoApiBackendTransactionUrl string = ''

@description('Public repository installed for the collector-hosted demo API.')
param demoApiSourceRepository string = collectorSourceRepository

@description('Exact reviewed commit installed for the collector-hosted demo API.')
param demoApiSourceRef string = collectorSourceRef

@description('Exact raw URL for the reviewed demo API installer script.')
param demoApiInstallerUri string = ''

var resourceSuffix = '${prefix}-${environment}'
var collectorName = 'vm-stcollector-${resourceSuffix}'
var collectorComputerName = 'stcollector-${environment}'
var collectorImage = loadJsonContent('../config/collector-image.json')
var bootstrapTemplate = loadTextContent('../bootstrap/collector-cloud-init.yaml')
var bootstrapWithRepository = replace(bootstrapTemplate, '__COLLECTOR_SOURCE_REPOSITORY__', collectorSourceRepository)
var bootstrapWithRef = replace(bootstrapWithRepository, '__COLLECTOR_SOURCE_REF__', collectorSourceRef)
var bootstrapWithPort = replace(bootstrapWithRef, '__COLLECTOR_PORT__', string(collectorPort))
var bootstrapWithPrivateIp = replace(bootstrapWithPort, '__COLLECTOR_PRIVATE_IP__', privateIpAddress)
var renderedBootstrap = replace(bootstrapWithPrivateIp, '__COLLECTOR_CERTIFICATE_NAME__', collectorComputerName)

resource demoApiPublicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = if (deployCollectorDemoApi) {
  name: 'pip-st-demo-api-${resourceSuffix}'
  location: location
  sku: {
    name: 'Standard'
  }
  tags: union(tags, {
    component: 'collector-hosted-demo-api'
    exposure: 'public-https'
  })
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
    dnsSettings: {
      domainNameLabel: demoApiDnsLabel
    }
  }
}

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
          publicIPAddress: deployCollectorDemoApi ? {
            id: demoApiPublicIp.id
          } : null
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
        publisher: collectorImage.publisher
        offer: collectorImage.offer
        sku: collectorImage.sku
        version: collectorImage.version
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

resource operationsNsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' existing = {
  name: operationsNsgName
}

resource allowDemoApiHttp 'Microsoft.Network/networkSecurityGroups/securityRules@2024-05-01' = if (deployCollectorDemoApi) {
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
    destinationAddressPrefix: privateIpAddress
  }
}

resource allowDemoApiHttps 'Microsoft.Network/networkSecurityGroups/securityRules@2024-05-01' = if (deployCollectorDemoApi) {
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
    destinationAddressPrefix: privateIpAddress
  }
}

resource demoApiExtension 'Microsoft.Compute/virtualMachines/extensions@2024-07-01' = if (deployCollectorDemoApi) {
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
        demoApiInstallerUri
      ]
      commandToExecute: 'bash install_collector_demo_api.sh ${demoApiSourceRepository} ${demoApiSourceRef} ${demoApiPublicIp.properties.dnsSettings.fqdn} ${demoApiBackendTransactionUrl} ${demoApiAllowedOrigin}'
    }
  }
  dependsOn: [
    collectorNic
    allowDemoApiHttp
    allowDemoApiHttps
  ]
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
output collectorDesiredImage object = collectorImage
output collectorDemoApiEnabled bool = deployCollectorDemoApi
output collectorDemoApiPublicIpId string = deployCollectorDemoApi ? demoApiPublicIp.id : ''
output collectorDemoApiFqdn string = deployCollectorDemoApi ? demoApiPublicIp.properties.dnsSettings.fqdn : ''
output collectorDemoApiHealthUrl string = deployCollectorDemoApi ? 'https://${demoApiPublicIp.properties.dnsSettings.fqdn}/api/health' : ''
output collectorDemoApiRunUrl string = deployCollectorDemoApi ? 'https://${demoApiPublicIp.properties.dnsSettings.fqdn}/api/demo/run' : ''
