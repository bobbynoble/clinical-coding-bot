# Clinical Coding Bot — Setup Guide

## 1. Azure resources to create (Portal)

### Azure AI Search
1. Portal → Create resource → "Azure AI Search"
2. Resource group: `rg-fhir-sandbox-rn`
3. Region: UK South
4. Pricing tier: **Basic** (needed for vector search)
5. Once deployed: go to resource → **Keys** → copy the Admin key and URL

### Azure OpenAI model deployments
In your existing Azure OpenAI resource:
1. Go to Azure OpenAI Studio → Deployments → New deployment
2. Deploy **gpt-4o** — name it `gpt-4o`
3. Deploy **text-embedding-3-large** — name it `text-embedding-3-large`

---

## 2. Configure environment

```
cp .env.example .env
```

Edit `.env` and fill in:
- `AZURE_OPENAI_ENDPOINT` — from your OpenAI resource → Keys and Endpoint
- `AZURE_OPENAI_API_KEY` — Key 1 from same page
- `AZURE_SEARCH_ENDPOINT` — from AI Search resource overview
- `AZURE_SEARCH_API_KEY` — Admin key from AI Search → Keys

---

## 3. Add coding reference data

See `data/README.md` for download links and expected CSV formats.
At minimum, download the free ICD-10-CM order file from CMS and save as `data/icd10.csv`.

---

## 4. Index the reference data

```bash
pip install -r requirements.txt
python -m app.indexer
```

This only needs to run once (or when you update the reference files).

---

## 5. Run locally (Python 3.12 recommended)

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000

---

## 6. Deploy to Azure App Service

### Create App Service (Portal)
1. Create resource → Web App
2. Resource group: `rg-fhir-sandbox-rn`
3. Runtime: **Python 3.12**
4. Region: UK South
5. Plan: B1 (sufficient to start)

### Deploy via az CLI
```bash
# Login
az login

# Zip deploy
Compress-Archive -Path * -DestinationPath deploy.zip -Force
az webapp deploy `
  --resource-group rg-fhir-sandbox-rn `
  --name <your-app-name> `
  --src-path deploy.zip `
  --type zip
```

### Set environment variables on App Service
Portal → App Service → Configuration → Application settings
Add each key from your `.env` file as an Application Setting.

Or via CLI:
```bash
az webapp config appsettings set `
  --resource-group rg-fhir-sandbox-rn `
  --name <your-app-name> `
  --settings AZURE_OPENAI_ENDPOINT="..." AZURE_OPENAI_API_KEY="..." ...
```

### Set startup command
Portal → App Service → Configuration → General settings → Startup command:
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
