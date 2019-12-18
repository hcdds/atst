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

variable "sku" {
    type = string
    description = "SKU of which CDN to use"
    default = "Standard_Verizon"
}

variable "origin_host_name" {
    type = string
    description = "Subdomain to use for the origin in requests to the CDN"
}

