variable "subscription_id" {
  description = "Azure subscription ID used by the AzureRM provider. Supply it through a local tfvars file or TF_VAR_subscription_id."
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Azure region for the lab resources."
  type        = string
  default     = "canadacentral"
}

variable "project_name" {
  description = "Short project identifier used in resource names and tags."
  type        = string
  default     = "azure-iac-msp-lab"
}

variable "environment" {
  description = "Environment label used in names and tags."
  type        = string
  default     = "demo"

  validation {
    condition     = contains(["demo", "dev", "test"], var.environment)
    error_message = "environment must be one of: demo, dev, test."
  }
}

variable "owner_tag" {
  description = "Non-sensitive ownership tag for cost and lifecycle tracking."
  type        = string
  default     = "portfolio-owner"
}

variable "vnet_address_space" {
  description = "Address space for the lab virtual network."
  type        = list(string)
  default     = ["10.20.0.0/16"]
}

variable "management_subnet_prefixes" {
  description = "Address prefixes for the management subnet."
  type        = list(string)
  default     = ["10.20.10.0/24"]
}

variable "server_subnet_prefixes" {
  description = "Address prefixes for the server subnet."
  type        = list(string)
  default     = ["10.20.20.0/24"]
}
