README — End-to-End Setup (Terraform + Docker + Azure Web App + GitHub Actions)

This project deploys:

Azure Container Registry (ACR) — stores Docker images

Azure App Service (Linux Web App for Containers) — runs the Docker image

Azure Key Vault (existing or optional) — stores OpenAI key securely

FastAPI app (inside test-llm-container/) — exposes /health, /sessions, /sessions/{id}/message

GitHub Actions — builds container and deploys automatically on every push to main

Repo structure

infra/ → Terraform code (Azure resources)

test-llm-container/ → Python FastAPI app + Dockerfile

.github/workflows/deploy.yml → GitHub Actions CI/CD

0) Prerequisites (install once)
On your laptop

Install:

Azure CLI (az)

Terraform

Docker Desktop

Git

Check:

az version
terraform -version
docker --version
git --version


Login to Azure:

az login
az account show

1) Clone repo
git clone https://github.com/Amui1234/test-llm-devops.git
cd test-llm-devops

2) Local test first (run app locally)

This ensures your code runs BEFORE Azure adds complexity.

2.1 Build and run container locally
cd test-llm-container
docker build -t rabo-llm-backend:local .
docker run --rm -p 8000:8000 \
  -e AZURE_OPENAI_CHAT_URL="YOUR_AZURE_OPENAI_CHAT_URL" \
  -e KEYVAULT_NAME="amrita" \
  -e KEYVAULT_SECRET_NAME="openai-api-key" \
  rabo-llm-backend:local


Now test:

curl -s http://localhost:8000/health


Expected:

{"status":"ok"}

If you don’t want KeyVault locally

Temporarily modify kv.py to read the API key from an env var for local runs:

OPENAI_API_KEY=...

(Then in Azure we keep KeyVault.)

3) Create infra in Azure (Terraform)

Go to Terraform folder:

cd ../infra

3.1 Set subscription (IMPORTANT)

Terraform provider needs subscription.

Run:

az account show --query id -o tsv


Copy the output (SUB_ID).

Where did this come from?

That long path like:
/subscriptions/<SUB_ID>/resourceGroups/<RG_NAME>
is the Azure resource ID. It’s how Azure uniquely identifies any resource. You can get it from:

az group show -n <RG_NAME> --query id -o tsv

3.2 Create/choose a Resource Group

If you already have one, skip.

az group create -n rg-devops-lab-Amrita -l westeurope

3.3 Update infra/terraform.tfvars

Open terraform.tfvars and set values like:

resource_group_name = "rg-devops-lab-Amrita"

location = "westeurope"

acr_name = "rabollmacr123" (must be globally unique)

webapp_name = "rabo-llm-app" (must be globally unique)

any KeyVault name etc.

3.4 Terraform init/plan/apply
terraform init
terraform validate
terraform plan
terraform apply


Terraform will show a plan and ask:

Only 'yes' will be accepted

Type:

yes

4) Build & push first image (bootstrap)

Why this is needed:

Terraform can create a Web App pointing to an image name…

BUT ACR is empty at first

So the Web App has nothing to run → “Application Error”

That’s why we push first image manually once.

4.1 Get ACR login server
ACR_LOGIN_SERVER=$(az acr show -n rabollmacr123 -g rg-devops-lab-Amrita --query loginServer -o tsv)
echo $ACR_LOGIN_SERVER


Expected like:

rabollmacr123.azurecr.io

4.2 Login to ACR
az acr login --name rabollmacr123

4.3 IMPORTANT (Mac M1/M2 users)

App Service runs linux/amd64 typically.
If you push an ARM image, Azure gives:

exec /usr/local/bin/uvicorn: exec format error

So build amd64:

cd ../test-llm-container

docker buildx create --use --name amd64builder || docker buildx use amd64builder

docker buildx build --platform linux/amd64 \
  -t $ACR_LOGIN_SERVER/rabo-llm-backend:bootstrap \
  --push .

4.4 Restart webapp
az webapp restart -g rg-devops-lab-Amrita -n rabo-llm-app

4.5 Test deployed app
HOST=$(az webapp show -g rg-devops-lab-Amrita -n rabo-llm-app --query defaultHostName -o tsv)
curl -s https://$HOST/health


Expected:

{"status":"ok"}

5) Test the LLM chat API (assignment requirement)
5.1 Create session
curl -s -X POST https://$HOST/sessions


Copy session_id.

5.2 Send a message
curl -s -X POST "https://$HOST/sessions/<SESSION_ID>/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello. Remember my name is Ali."}'

5.3 Ask memory question
curl -s -X POST "https://$HOST/sessions/<SESSION_ID>/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is my name?"}'


Expected:

{"ended":false,"assistant":{"answer":"Your name is Ali.","actions":[],"follow_up_questions":[]}}

5.4 End session
curl -s -X POST "https://$HOST/sessions/<SESSION_ID>/message" \
  -H "Content-Type: application/json" \
  -d '{"message":"end"}'


After ending, if you ask again:

{"detail":"Session not found or ended"}

6) Key Vault permissions (why + how)
Why do we do role assignment?

Your Web App uses System Assigned Managed Identity to authenticate to Azure.

Key Vault has secrets. Azure will block access unless you grant permission.

You assign:

Key Vault Secrets User (or Key Vault Secrets Officer if needed)
to the Web App’s managed identity on the Key Vault scope.

How to do it via CLI

Get Web App identity principal id:

PRINCIPAL_ID=$(az webapp identity show -g rg-devops-lab-Amrita -n rabo-llm-app --query principalId -o tsv)
echo $PRINCIPAL_ID


Assign permission:

az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<SUB_ID>/resourceGroups/<RG_NAME>/providers/Microsoft.KeyVault/vaults/<KEYVAULT_NAME>"

How to check it
az role assignment list --assignee "$PRINCIPAL_ID" --all -o table

Can I do this from Azure Portal?

Yes:

Key Vault → Access control (IAM) → Add role assignment

Role: Key Vault Secrets User

Assign access to: Managed identity

Select subscription → App Service → your webapp → Save

7) GitHub Actions auto-deploy (no manual docker after this)

After bootstrap, GitHub Actions will:

build docker image with tag = commit SHA

push to ACR

point Web App to that exact SHA tag

restart the app

7.1 Create Service Principal for GitHub Actions
az ad sp create-for-rbac \
  --name "rabo-llm-gha" \
  --role "Contributor" \
  --scopes /subscriptions/<SUB_ID>/resourceGroups/rg-devops-lab-Amrita


It outputs:

appId = AZURE_CLIENT_ID

password = AZURE_CLIENT_SECRET

tenant = AZURE_TENANT_ID

And your subscription id:

az account show --query id -o tsv


= AZURE_SUBSCRIPTION_ID

7.2 Grant SP permission to push to ACR
ACR_ID=$(az acr show -g rg-devops-lab-Amrita -n rabollmacr123 --query id -o tsv)

az role assignment create \
  --assignee "<appId>" \
  --role "AcrPush" \
  --scope "$ACR_ID"

7.3 Add GitHub Secrets (THIS IS REQUIRED)

Yes — you must set secrets, because GitHub Actions runs on GitHub servers, not your laptop, so it needs credentials.

Go to:
Repo → Settings → Secrets and variables → Actions → New repository secret

Add:

AZURE_CLIENT_ID = appId

AZURE_CLIENT_SECRET = password

AZURE_TENANT_ID = tenant

AZURE_SUBSCRIPTION_ID = your subscription id

And infra names:

RESOURCE_GROUP = rg-devops-lab-Amrita

ACR_NAME = rabollmacr123

WEBAPP_NAME = rabo-llm-app

7.4 How to see the latest deployed image tag
Option A: Check Web App container setting
az webapp config container show -g rg-devops-lab-Amrita -n rabo-llm-app --query linuxFxVersion -o tsv


You will see something like:

DOCKER|rabollmacr123.azurecr.io/rabo-llm-backend:<SHA>


That <SHA> is the deployed tag.

Option B: List ACR tags
az acr repository show-tags -n rabollmacr123 --repository rabo-llm-backend -o table

8) .gitignore (IMPORTANT — avoid committing junk)

.gitignore is a file, not a folder.

Create it:

touch .gitignore


Recommended contents:

# mac
.DS_Store

# terraform
infra/.terraform/
infra/.terraform.lock.hcl
infra/terraform.tfstate
infra/terraform.tfstate.backup

# python
__pycache__/
*.pyc

# env
.env


Why:

.terraform/ is huge provider binaries

terraform.tfstate contains sensitive resource info

.DS_Store is useless mac metadata

9) Common problems & fixes
“exec /usr/local/bin/uvicorn: exec format error”

Cause: built ARM image on M1/M2 Mac.

Fix:

docker buildx build --platform linux/amd64 ...

Web App shows “Application Error”

Check logs:

az webapp log tail -g rg-devops-lab-Amrita -n rabo-llm-app

GitHub push keeps using old GitHub user / 403

You must update credential stored in mac keychain.

One quick method (forces prompt):

GIT_TERMINAL_PROMPT=1 GIT_ASKPASS= git -c credential.helper= push


When it asks password:

paste a PAT (Personal Access Token), not your GitHub password

Create PAT:
GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
Scopes: repo
