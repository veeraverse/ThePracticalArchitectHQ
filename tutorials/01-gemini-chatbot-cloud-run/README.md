# 01 · Deploy a Gemini AI chatbot on Cloud Run

▶️ Watch: [VIDEO_LINK]

## What you'll build

A FastAPI web chatbot that calls Gemini on Vertex AI, deployed to a public Cloud Run URL.

## Architecture

```
Browser → Cloud Run (FastAPI) → Vertex AI (Gemini)
```

The app uses the [google-genai](https://pypi.org/project/google-genai/) SDK, not the deprecated `vertexai.generative_models` module.

## Prerequisites

- A Google Cloud project with billing enabled
- The gcloud CLI, or Google Cloud Shell
- Python 3.12

## Setup

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Skip this in Cloud Shell
gcloud auth application-default login

export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

## Run locally

Check that Gemini responds:

```bash
python test.py
```

Then start the web app and open http://localhost:8000:

```bash
uvicorn main:app --reload
```

## Deploy

Grant the Cloud Run runtime service account permission to call Vertex AI, then deploy from source:

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud run deploy gemini-chatbot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1
```

Get the service URL:

```bash
gcloud run services describe gemini-chatbot --region us-central1 --format='value(status.url)'
```

> **Production note:** Use a dedicated service account with only `roles/aiplatform.user` instead of the default compute service account, and add authentication in front of the service. `--allow-unauthenticated` means anyone with the URL can use it on your billing.

## Clean up

```bash
gcloud run services delete gemini-chatbot --region us-central1
```

## Cost note

Cloud Run scales to zero when idle; Gemini calls are billed per token. A few test messages cost very little.

## Troubleshooting

- **Permission denied calling Vertex AI from Cloud Run** → the IAM binding in [Deploy](#deploy) is missing.
- **`KeyError: 'GOOGLE_CLOUD_PROJECT'`** → export it locally, or check `--set-env-vars` on deploy.
- **Container failed to start** → check the `Procfile` name and contents.
- **Model not found** → check the current Gemini model names in the Vertex AI docs and update `MODEL` in `main.py`.
