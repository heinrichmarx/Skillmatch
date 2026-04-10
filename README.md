# SkillMatch — Azure Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        Azure                            │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │  Azure Static   │    │  Azure Static Web App       │ │
│  │  Web App        │    │  recruiter-portal/          │ │
│  │  candidate-     │    │  index.html                 │ │
│  │  portal/        │    └──────────────┬──────────────┘ │
│  │  index.html     │                   │                │
│  └────────┬────────┘                   │                │
│           │  HTTPS REST API            │                │
│           └───────────────┬────────────┘                │
│                           ▼                             │
│              ┌────────────────────────┐                 │
│              │  Azure App Service     │                 │
│              │  (Python / Flask API)  │                 │
│              │  /api/candidates       │                 │
│              │  /api/jobs             │                 │
│              │  /api/jobs/{id}/matches│                 │
│              └────────────┬───────────┘                 │
│                           │ pyodbc                      │
│                           ▼                             │
│              ┌────────────────────────┐                 │
│              │  Azure SQL Database    │                 │
│              │  candidates            │                 │
│              │  candidate_skills      │                 │
│              │  job_requirements      │                 │
│              │  required_skills       │                 │
│              └────────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
skillmatch/
├── backend/
│   ├── app.py              ← Flask API + matching engine
│   ├── requirements.txt    ← Python dependencies
│   └── web.config          ← Azure App Service config
├── candidate-portal/
│   └── index.html          ← Candidate skill registration SPA
├── recruiter-portal/
│   └── index.html          ← Recruiter search + results SPA
└── infrastructure/
    └── main.bicep          ← Azure IaC (SQL + App Service + Static Web Apps)
```

---

## Step 1 — Prerequisites

```bash
# Install Azure CLI
brew install azure-cli   # macOS
# or: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

az login
az account set --subscription <your-subscription-id>
```

---

## Step 2 — Deploy Azure Infrastructure

```bash
# Create a resource group
az group create --name skillmatch-rg --location australiaeast

# Deploy all resources (SQL + App Service + Static Web Apps)
az deployment group create \
  --resource-group skillmatch-rg \
  --template-file infrastructure/main.bicep \
  --parameters environment=prod sqlAdminPassword=<YourStr0ngP@ssword>

# Note the outputs: apiUrl, candidatePortalUrl, recruiterPortalUrl
```

---

## Step 3 — Deploy the API

```bash
cd backend

# Zip and deploy to Azure App Service
zip -r ../api.zip .
az webapp deployment source config-zip \
  --resource-group skillmatch-rg \
  --name skillmatch-prod-api \
  --src ../api.zip
```

---

## Step 4 — Configure API URL in Portals

Before deploying the frontends, set the API endpoint in each HTML file:

**candidate-portal/index.html** — add before `</body>`:
```html
<script>window.SKILLMATCH_API = 'https://skillmatch-prod-api.azurewebsites.net';</script>
```

**recruiter-portal/index.html** — same script tag.

Or set via Azure Static Web App environment variable / `staticwebapp.config.json`.

---

## Step 5 — Deploy Static Web Apps

**Option A: GitHub Actions (recommended)**

1. Push this repo to GitHub
2. In Azure Portal → Static Web App → Deployment → Connect to GitHub
3. Set `app_location` to `/candidate-portal` and `/recruiter-portal` respectively
4. GitHub Actions workflows are auto-generated

**Option B: Azure CLI**

```bash
# Deploy candidate portal
az staticwebapp deploy \
  --name skillmatch-prod-candidate \
  --resource-group skillmatch-rg \
  --source candidate-portal \
  --token <deployment-token>

# Deploy recruiter portal
az staticwebapp deploy \
  --name skillmatch-prod-recruiter \
  --resource-group skillmatch-rg \
  --source recruiter-portal \
  --token <deployment-token>
```

---

## Step 6 — Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py
# API runs at http://localhost:5000

# Frontend (any static server)
cd candidate-portal && npx serve .
cd recruiter-portal  && npx serve .
```

---

## Database Schema

| Table              | Purpose                                      |
|--------------------|----------------------------------------------|
| `candidates`       | Candidate profiles, preferences, experience  |
| `candidate_skills` | Skill entries with level + years per candidate |
| `job_requirements` | Recruiter job postings with criteria         |
| `required_skills`  | Skill requirements per job (required/optional)|

---

## Matching Algorithm

The engine scores each candidate against a job using:

- **Per skill**: `(level_ratio × 0.6) + (years_ratio × 0.4)`
  - `level_ratio`: candidate level vs required minimum (novice=1, capable=2, expert=3)
  - `years_ratio`: candidate years / required years (capped at 1.0)
- **Required skills** are weighted 2× vs optional skills
- **IT experience bonus**: up to 5 extra points for overall experience
- Final score is capped at 100%

---

## Cost Estimate (Azure, prod)

| Resource             | SKU     | Est. Monthly Cost |
|----------------------|---------|-------------------|
| Azure SQL            | Basic   | ~$5               |
| App Service Plan     | B1      | ~$14              |
| Static Web Apps (×2) | Free    | $0                |
| **Total**            |         | **~$19/month**    |

Upgrade SQL to S2 + App Service to P1 for production workloads.

---

## Security Checklist

- [ ] Rotate `sqlAdminPassword` and store in Azure Key Vault
- [ ] Enable Azure AD authentication on SQL (remove SQL login)
- [ ] Add authentication to recruiter portal (Azure AD B2C or Static Web App auth)
- [ ] Enable HTTPS-only on App Service
- [ ] Set CORS to specific portal domains only
- [ ] Enable Azure Defender for SQL
- [ ] Add rate limiting to the API (use Azure API Management)
