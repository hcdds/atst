data "azurerm_key_vault_secret" "keyvault_atat_password" {
  name         = "postgres-atat-password"
  key_vault_id = module.operator_keyvault.id
}

module "keyvault" {
  source                  = "../../modules/keyvault"
  name                    = "cz"
  region                  = var.region
  owner                   = var.owner
  environment             = var.environment
  tenant_id               = var.tenant_id
  principal_id            = "f9bcbe58-8b73-4957-aee2-133dc3e58063"
  admin_principals        = var.admin_users
  secret_pgpassword_value = data.azurerm_key_vault_secret.keyvault_atat_password.value
}
