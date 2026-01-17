#Key Vault secret fetch.Hardcoding API keys in code or GitHub secrets is dangerous.In banks, secrets must be stored in Key Vault, rotated, audited.
from functools import lru_cache 
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

KEYVAULT_NAME = os.getenv("KEYVAULT_NAME", "amrita")
SECRET_NAME   = os.getenv("KEYVAULT_SECRET_NAME", "openai-api-key")

@lru_cache(maxsize=1) #Key Vault calls are network calls and can be slow/limited. So we fetch secret once and reuse in memory.
def get_openai_api_key() -> str:
    vault_url = f"https://amrita.vault.azure.net/"
    cred = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=cred)
    return client.get_secret(SECRET_NAME).value

#What happens at runtime

# Inside Azure App Service:

# your web app has a Managed Identity

# Key Vault gives that identity permission (RBAC)

# Python uses DefaultAzureCredential() which automatically uses managed identity

# So kv.py does:

# build vault URL: https://open-ai-keys-rob.vault.azure.net

# authenticate using managed identity

# read secret named openai-api-key

# returns the API key string
