locals {
  name_prefix = "aia-${var.environment}"

  common_tags = {
    project     = var.project_name
    environment = var.environment
    owner       = var.owner_tag
    managed_by  = "terraform"
    purpose     = "msp-portfolio-lab"
  }
}
