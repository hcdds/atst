# Task order bucket is required to be accessible publicly by the users.
# which is why the policy here is "Allow"
module "task_order_bucket" {
  source       = "../../modules/bucket"
  service_name = "jeditasksatat"
  owner        = var.owner
  name         = var.name
  environment  = var.environment
  region       = var.region
  policy       = "Allow"
  subnet_ids   = [module.vpc.subnets]
  whitelist    = var.storage_admin_whitelist
}

# TF State should be restricted to admins only, but IP protected
# This has to be public due to a chicken/egg issue of VPN not 
# existing until TF is run. If this bucket is private, you would
# not be able to access it when running TF without being on a VPN.
module "tf_state" {
  source       = "../../modules/bucket"
  service_name = "jedidevtfstate"
  owner        = var.owner
  name         = var.name
  environment  = var.environment
  region       = var.region
  policy       = "Deny"
  subnet_ids   = []
  whitelist    = var.storage_admin_whitelist
}
