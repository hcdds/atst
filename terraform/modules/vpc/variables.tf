variable "environment" {
  description = "Environment (Prod,Dev,etc)"
}

variable "region" {
  description = "Region (useast2, etc)"

}

variable "name" {
  description = "Name or prefix to use for all resources created by this module"
}

variable "owner" {
  description = "Owner of these resources"

}

variable "ddos_enabled" {
  description = "Enable or disable DDoS Protection (1,0)"
  default     = "0"
}

variable "virtual_network" {
  description = "The supernet used for this VPC a.k.a Virtual Network"
  type        = string
}

variable "networks" {
  description = "A map of lists describing the network topology"
  type        = map
}

variable "dns_servers" {
  description = "DNS Server IPs for internal and public DNS lookups (must be on a defined subnet)"
  type        = list

}

variable "route_tables" {
  type        = map
  description = "A map with the route tables to create"
}

variable "gateway_subnet" {
  type        = string
  description = "The Subnet CIDR that we'll use for the virtual_network_gateway 'GatewaySubnet'"
}

variable "service_endpoints" {
  type        = map
  description = "A map of the service endpoints and its mapping to subnets"

}

variable "vpn_client_cidr" {
  type        = list
  description = "The CIDR range used for clients on the VPN"
  default     = ["172.16.0.0/16"]
}
