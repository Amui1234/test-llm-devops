# Rabo LLM DevOps Assignment – Complete End-to-End Guide

> **Audience:**  
> Absolute beginners to DevOps, Cloud, Terraform, and CI/CD  
> Interviewers evaluating real-world DevOps understanding  
>
> **Goal:**  
> Clone this repository → create infrastructure → deploy an LLM-backed API → test it end-to-end → understand *why* everything exists

---

## 1. What Is This Project?

This project implements a **production-style LLM API** using:

- **FastAPI** (backend REST API)
- **Azure OpenAI** (LLM)
- **Docker** (containerization)
- **Azure App Service** (hosting)
- **Azure Container Registry (ACR)** (image storage)
- **Azure Key Vault** (secret management)
- **Terraform** (infrastructure as code)
- **GitHub Actions** (CI/CD automation)

Everything is automated and reproducible.

---

## 2. What Problem Does This Solve?

In real companies:

- Developers should **not deploy manually**
- Secrets should **never live in code**
- Infrastructure should be **reproducible**
- Deployments should be **immutable**
- LLM services must **remember context**
- Changes should deploy automatically

This assignment demonstrates **all of the above**.

---

## 3. High-Level Architecture (Mental Model)



Your Laptop
|
| git push
v
GitHub Repository
|
| GitHub Actions (CI/CD)
v
Azure Container Registry (Docker Images)
|
| Pull Image
v
Azure App Service (Linux Container)
|
| HTTPS
v
FastAPI Application
|
| HTTPS
v
Azure OpenAI


---

## 4. Repository Structure (Very Important)



test-llm-devops/
│
├── infra/ # Terraform: Azure infrastructure
│ ├── providers.tf # Azure provider config
│ ├── versions.tf # Terraform versions
│ ├── variables.tf # Input variables
│ ├── outputs.tf # Values printed after apply
│ ├── acr.tf # Azure Container Registry
│ ├── appservice.tf # Azure App Service
│ ├── iam.tf # Permissions & identities
│ └── data.tf # Existing Azure data lookups
│
├── test-llm-container/ # Application code
│ ├── Dockerfile # Container definition
│ ├── requirements.txt # Python dependencies
│ ├── app.py # FastAPI REST API
│ ├── llm.py # Azure OpenAI client
│ ├── kv.py # Azure Key Vault access
│ ├── db.py # SQLite session storage
│ └── readme.md
│
├── .github/workflows/
│ └── deploy.yml # CI/CD pipeline
│
├── .gitignore
└── README.md


---

## 5. Prerequisites (Install Once)

### 5.1 Git
```bash
git --version

5.2 Docker

Install Docker Desktop
Verify:

docker --version

5.3 Azure CLI
brew install azure-cli
az login

5.4 Terraform
brew install terraform
terraform -version

6. Step 1 – Clone the Repository
git clone https://github.com/Amui1234/test-llm-devops.git
cd test-llm-devops


At this point nothing exists in Azure yet.

7. Step 2 – Infrastructure Creation (Terraform)
Why Terraform?

No clicking in Azure Portal

Repeatable setup

Version controlled infrastructure

Interview-friendly

7.1 Go to Infra Folder
cd infra

7.2 Understand What Terraform Will Create

Terraform creates:

Resource	Purpose
Resource Group	Logical container
ACR	Stores Docker images
App Service Plan	Compute
App Service	Runs container
Key Vault	Stores secrets
Managed Identity	Secure auth
IAM Roles	Least privilege
7.3 Initialize Terraform
terraform init


Downloads Azure provider and prepares state.

7.4 Apply Terraform
terraform apply


Type yes when prompted.

After completion, Terraform prints important outputs like:

Resource Group name

ACR name

Web App name

Key Vault name

⚠️ These values are used later in GitHub Actions

8. Step 3 – Run Application Locally (Before Cloud)
Why test locally?

Never deploy broken code to cloud.

8.1 Build Docker Image
cd ../test-llm-container
docker build -t rabo-llm-backend:local .

8.2 Run Container
docker run -p 8000:8000 rabo-llm-backend:local

8.3 Test Health Endpoint
curl http://localhost:8000/health


Expected:

{"status":"ok"}

9. Step 4 – Secrets & Security (Key Vault)
Why Key Vault?

No API keys in GitHub

No secrets in Docker image

No secrets in environment files

How It Works

Terraform creates Key Vault

Azure App Service has Managed Identity

App uses DefaultAzureCredential

Key Vault allows identity to read secrets

Secrets never leave Azure

10. Step 5 – CI/CD Authentication (Service Principal)

GitHub Actions must talk to Azure.

10.1 Create Service Principal
az ad sp create-for-rbac \
  --name "rabo-llm-gha" \
  --role "Contributor" \
  --scopes /subscriptions/<SUB_ID>/resourceGroups/<RG>


Save this output carefully:

{
  "appId": "...",
  "password": "...",
  "tenant": "..."
}

11. Step 6 – GitHub Secrets

Go to GitHub → Repo → Settings → Secrets → Actions

Add:

Secret	Meaning
AZURE_CLIENT_ID	appId
AZURE_CLIENT_SECRET	password
AZURE_TENANT_ID	tenant
AZURE_SUBSCRIPTION_ID	subscription
ACR_NAME	From Terraform output
WEBAPP_NAME	From Terraform output
RESOURCE_GROUP	From Terraform output
12. Step 7 – CI/CD Pipeline (deploy.yml)

On every push to main:

GitHub logs into Azure

Builds Docker image

Tags with Git SHA (immutable)

Pushes to ACR

Updates Web App container

Restarts app

No manual deployment after this.

13. Step 8 – Verify Cloud Deployment
HOST=$(az webapp show \
  -g <RESOURCE_GROUP> \
  -n <WEBAPP_NAME> \
  --query defaultHostName -o tsv)

curl https://$HOST/health


Expected:

{"status":"ok"}

14. Step 9 – LLM API Usage (Assignment Core)
Create Session
curl -X POST https://$HOST/sessions


Returns:

{"session_id":"UUID"}

Send Message
curl -X POST https://$HOST/sessions/<SESSION_ID>/message \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, remember my name is Ali"}'

Ask Follow-Up
curl -X POST https://$HOST/sessions/<SESSION_ID>/message \
  -d '{"message":"What is my name?"}'


LLM remembers conversation history.

End Session
curl -X POST https://$HOST/sessions/<SESSION_ID>/message \
  -d '{"message":"end"}'

15. Why Each Component Exists (Interview Gold)
Component	Reason
FastAPI	Async, modern API
Docker	Immutable deploys
Terraform	Reproducible infra
Key Vault	Secure secrets
Managed Identity	No credentials
ACR	Image versioning
GitHub Actions	Automation
App Service	Low ops overhead
16. Common Interview Questions

Q: Why not store secrets in GitHub?
A: Security risk, audit failure.

Q: Why Docker instead of zip deploy?
A: Environment consistency.

Q: How does LLM remember context?
A: Session history stored in SQLite.

Q: What happens on rollback?
A: Redeploy previous image tag.

Q: Why not VM?
A: App Service reduces ops burden.

17. Final Outcome

✅ Zero manual deployment
✅ Secure secrets
✅ Automated CI/CD
✅ Production-grade design
✅ Interview-ready explanation

18. How to Reproduce From Scratch

Clone repo

Install tools

Terraform apply

Add GitHub secrets

Push code

Test API

That’s it.