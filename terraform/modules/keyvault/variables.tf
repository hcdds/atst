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
  description = "Owner of this environment"
}

variable "tenant_id" {
  type        = string
  description = "The Tenant ID"
}

variable "principal_id" {
  type        = string
  description = "The service principal_id of the k8s cluster"
}

variable "admin_principals" {
  type        = map
  description = "A list of user principals who need access to manage the keyvault"
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