data "azurerm_resource_group" "rg" {
  name = var.rg_name
}
#You are NOT creating a resource group.You are reading an existing one.This is exactly what “use existing RG” means
#Because you must use an existing resource group: Terraform does NOT create one.