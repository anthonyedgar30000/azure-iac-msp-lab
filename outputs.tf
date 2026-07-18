output "resource_group_name" {
  description = "Name of the network foundation resource group."
  value       = azurerm_resource_group.lab.name
}

output "virtual_network_name" {
  description = "Name of the lab virtual network."
  value       = azurerm_virtual_network.lab.name
}

output "subnet_ids" {
  description = "Subnet IDs keyed by functional role."
  value = {
    management = azurerm_subnet.management.id
    servers    = azurerm_subnet.servers.id
  }
}

output "network_security_group_ids" {
  description = "Network security group IDs keyed by functional role."
  value = {
    management = azurerm_network_security_group.management.id
    servers    = azurerm_network_security_group.servers.id
  }
}
