# Setup Weaviate Environment Variables

## Overview

The v2.0 search functionality requires Weaviate credentials to be set as environment variables. There are two ways to set them:

1. **During deployment** (recommended) - Set them when deploying the function
2. **Via Google Cloud Console** - Update them after deployment

## Option 1: Set During Deployment (Recommended)

Add the Weaviate environment variables to your deployment command:

```bash
gcloud functions deploy search \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./functions \
  --entry-point=router \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=300s \
  --max-instances=3 \
  --min-instances=0 \
  --set-env-vars HF_TOKEN=your_hf_token_here,WEAVIATE_URL=your_weaviate_url,WEAVIATE_API_KEY=your_weaviate_api_key
```

**Important:** Replace:
- `your_hf_token_here` with your HuggingFace token
- `your_weaviate_url` with your Weaviate cluster URL (e.g., `https://your-cluster.weaviate.network` or just `your-cluster.weaviate.network`)
- `your_weaviate_api_key` with your Weaviate API key

### Example:

```bash
gcloud functions deploy search \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./functions \
  --entry-point=router \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=300s \
  --max-instances=3 \
  --min-instances=0 \
  --set-env-vars HF_TOKEN=hf_abc123...,WEAVIATE_URL=https://b6rliny3qchbav0dlxw.c0.us-west3.gcp.weaviate.cloud,WEAVIATE_API_KEY=your-api-key-here
```

## Option 2: Update After Deployment (Google Cloud Console)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Cloud Functions** → **search** function
3. Click **Edit** (pencil icon)
4. Scroll down to **Runtime, build, connections and security settings**
5. Expand **Runtime environment variables**
6. Click **Add Variable** for each:
   - `WEAVIATE_URL` = your Weaviate cluster URL
   - `WEAVIATE_API_KEY` = your Weaviate API key
7. Click **Deploy** to save changes

## Option 3: Update via gcloud CLI

You can also update environment variables without redeploying the entire function:

```bash
gcloud functions deploy search \
  --gen2 \
  --region=us-central1 \
  --update-env-vars WEAVIATE_URL=your_weaviate_url,WEAVIATE_API_KEY=your_weaviate_api_key
```

**Note:** This will update only the environment variables, not redeploy the code.

## For Local Testing

For local testing with `functions-framework`, you can set environment variables in your shell:

```bash
export WEAVIATE_URL="https://your-cluster.weaviate.network"
export WEAVIATE_API_KEY="your-api-key"
export HF_TOKEN="your-hf-token"

cd functions
functions-framework --target=router --port=8080
```

Or create a `.env` file in the `functions/` directory (for local use only):

```bash
# functions/.env (for local testing only - NOT used by Cloud Functions)
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-api-key
HF_TOKEN=your-hf-token
```

Then load it before running:

```bash
cd functions
export $(cat .env | xargs)
functions-framework --target=router --port=8080
```

**Important:** The `.env` file is for local testing only. Cloud Functions will NOT read it. You must set environment variables during deployment or via the console.

## Getting Your Weaviate Credentials

1. **Weaviate URL**: 
   - Found in your Weaviate Cloud dashboard
   - Format: `https://your-cluster-id.weaviate.network` or just `your-cluster-id.weaviate.network`
   - The code will automatically add `https://` if missing

2. **Weaviate API Key**:
   - Found in your Weaviate Cloud dashboard under API Keys
   - Create a new API key if you don't have one
   - Keep it secret!

## Verify Environment Variables Are Set

After deployment, verify the variables are set:

```bash
gcloud functions describe search --gen2 --region=us-central1 --format="value(serviceConfig.environmentVariables)"
```

Or test the function:

```bash
curl -G "https://us-central1-genesis-melodies.cloudfunctions.net/search" \
  --data-urlencode "model_name=english_st" \
  --data-urlencode "chunking_level=pericope" \
  --data-urlencode "top_k=5" \
  --data-urlencode 'search_verses=[{"chapter":1,"verse":1}]'
```

If the variables are missing, you'll get an error like:
```
ValueError: WEAVIATE_URL and WEAVIATE_API_KEY must be set in environment variables
```

## Security Notes

- ✅ Environment variables in Cloud Functions are secure and not exposed in logs
- ✅ Never commit API keys or tokens to git
- ✅ Use different keys for development and production if needed
- ✅ Rotate keys periodically for security

