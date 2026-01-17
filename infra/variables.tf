variable "rg_name" {
  type        = string
  description = "Existing resource group name"
}

variable "app_name" {
  type        = string
  description = "Web App name"
}

variable "acr_name" {
  type        = string
  description = "ACR name (must be globally unique)"
}

variable "keyvault_id" {
  type        = string
  description = "Resource ID of the existing Key Vault"
}
variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
}