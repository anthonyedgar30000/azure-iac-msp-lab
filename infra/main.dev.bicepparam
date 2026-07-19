using './main.bicep'

param prefix = 'mst'
param environment = 'dev'
param location = 'canadacentral'
param virtualNetworkAddressPrefix = '10.20.0.0/16'
param remoteUserVirtualNetworkAddressPrefix = '10.30.0.0/16'
param vpnClientAddressPrefix = '10.90.0.0/24'
