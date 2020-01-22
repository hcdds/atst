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

variable "secret_pgpassword_name" {
  type        = string
  description = "The name for the Key Vault secret for the password for the ATAT database user."
  default     = "PGPASSWORD"
}

variable "secret_pgpassword_value" {
  type        = string
  description = "The value for the Key Vault secret for the password for the ATAT database user."
}
