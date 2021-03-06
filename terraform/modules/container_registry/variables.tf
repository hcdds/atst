variable "region" {
  type        = string
  description = "Region this module and resources will be created in"
}

variable "name" {
  type        = string
  description = "Unique name for the services in this module"
}

variable "environment" {
  type        = string
  description = "Environment these resources reside (prod, dev, staging, etc)"
}

variable "owner" {
  type        = string
  description = "Owner of the environment and resources created in this module"
}

variable "backup_region" {
  type        = string
  description = "Backup region for georeplicating the container registry"
}

variable "sku" {
  type        = string
  description = "SKU to use for the container registry service"
  default     = "Premium"
}

variable "admin_enabled" {
  type        = string
  description = "Admin enabled? (true/false default: false)"
  default     = false

}

variable "subnet_ids" {
  description = "List of subnet_ids that will have access to this service"
  type        = list
}

variable "policy" {
  description = "The default policy for the network access rules (Allow/Deny)"
  default     = "Deny"
  type        = string
}

variable "whitelist" {
  type        = map
  description = "A map of whitelisted IPs and CIDR ranges. For single IPs, Azure expects just the IP, NOT a /32."
  default     = {}
}
