resource "azurerm_service_plan" "plan" {
  name                = "${var.app_name}-plan"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_linux_web_app" "app" {
  name                = var.app_name
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on = true

    application_stack {
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
      docker_image_name        = "rabo-llm-backend:latest"
    }
  }

  app_settings = {
    KEYVAULT_NAME         = "amrita"
    KEYVAULT_SECRET_NAME  = "openai-api-key"
    AZURE_OPENAI_CHAT_URL = "https://amritainterview.cognitiveservices.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-05-01-preview"
  }
}
