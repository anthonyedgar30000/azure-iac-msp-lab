using './main.bicep'

param prefix = 'mst'
param environment = 'dev'
param location = 'canadacentral'
param virtualNetworkAddressPrefix = '10.20.0.0/16'
param remoteUserVirtualNetworkAddressPrefix = '10.30.0.0/16'
param vpnClientAddressPrefix = '10.90.0.0/24'

// Keep compute and the public report endpoint disabled in the committed development
// parameter file. Enable them in a local secure parameter override and provide
// collectorAdminSshPublicKey explicitly.
param deployDemoBackends = false
param demoBackendVmSize = 'Standard_B1s'
param deployOperationsCollector = false
param deployPublicReportEndpoint = false
param publicReportAllowedOrigins = [
  'https://anthonyedgar30000.github.io'
]
param collectorPrivateIpAddress = '10.20.40.10'
param collectorVmSize = 'Standard_B1ms'
param collectorDataDiskSizeGb = 32
param collectorPort = 8080
param collectorSourceRepository = 'https://github.com/anthonyedgar30000/azure-iac-msp-lab.git'
param collectorSourceRef = 'main'
