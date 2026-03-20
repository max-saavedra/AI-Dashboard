# GCP Deployment Guide – IA Dashboard Backend

This document covers deploying the backend from an Ubuntu Server to
Google Cloud Run via Docker + Artifact Registry.

---

## Prerequisites

- Ubuntu Server 22.04 LTS
- Docker 24+
- Google Cloud SDK (`gcloud`) installed and authenticated
- A GCP project with billing enabled

---

## 1. Install Docker on Ubuntu Server

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) \
    signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER   # re-login after this
```

---

## 2. Install and Configure gcloud

```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## 3. Create GCP Resources (one-time)

```bash
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project $PROJECT_ID

# Create Artifact Registry repository
gcloud artifacts repositories create ia-dashboard \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID
```

---

## 4. Store Secrets in GCP Secret Manager

Never put secrets in environment variables directly. Store them in
Secret Manager and inject them into Cloud Run at deploy time.

```bash
echo -n "your-gemini-key" | \
    gcloud secrets create gemini-api-key \
    --data-file=- --project=$PROJECT_ID

echo -n "your-openai-key" | \
    gcloud secrets create openai-api-key \
    --data-file=- --project=$PROJECT_ID

echo -n "postgresql+asyncpg://user:pass@host:5432/db" | \
    gcloud secrets create database-url \
    --data-file=- --project=$PROJECT_ID

# Repeat for: app-secret-key, supabase-url,
#             supabase-anon-key, supabase-service-role-key
```

---

## 5. Build and Push the Docker Image

```bash
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/ia-dashboard/ia-dashboard-api:latest"

docker build -t "$IMAGE" .
docker push "$IMAGE"
```

---

## 6. Deploy to Cloud Run

```bash
gcloud run deploy ia-dashboard-api \
    --image "$IMAGE" \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --set-env-vars "APP_ENV=production" \
    --update-secrets \
        GEMINI_API_KEY=gemini-api-key:latest,\
        OPENAI_API_KEY=openai-api-key:latest,\
        DATABASE_URL=database-url:latest,\
        APP_SECRET_KEY=app-secret-key:latest,\
        SUPABASE_URL=supabase-url:latest,\
        SUPABASE_ANON_KEY=supabase-anon-key:latest,\
        SUPABASE_SERVICE_ROLE_KEY=supabase-service-role-key:latest \
    --project $PROJECT_ID
```

---

## 7. Run Database Migrations

After first deploy, run the initial schema against your Supabase project:

1. Go to Supabase Dashboard > SQL Editor
2. Paste the contents of `scripts/migrations/001_initial_schema.sql`
3. Click Run

---

## 8. Verify the Deployment

```bash
SERVICE_URL=$(gcloud run services describe ia-dashboard-api \
    --region $REGION --format="value(status.url)")

curl "$SERVICE_URL/api/v1/health"
# Expected: {"status":"ok","version":"1.0.0"}
```

---

## Local Development (without GCP)

```bash
cp .env.example .env
# Fill in your API keys in .env

# Start with Docker Compose (includes local Postgres)
docker compose up --build

# Or run directly with uvicorn (needs local Postgres)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| GEMINI_API_KEY | Yes | Google Gemini API key |
| OPENAI_API_KEY | Yes | OpenAI API key (fallback) |
| DATABASE_URL | Yes | asyncpg connection string |
| APP_SECRET_KEY | Yes | JWT validation secret |
| SUPABASE_URL | Yes | Supabase project URL |
| SUPABASE_ANON_KEY | Yes | Supabase anon public key |
| SUPABASE_SERVICE_ROLE_KEY | Yes | Supabase service role key |
| APP_ENV | No | development / production |
| APP_DEBUG | No | true / false |
| AI_TIMEOUT_SECONDS | No | Default: 8 |
| MAX_FILE_SIZE_MB | No | Default: 10 |
