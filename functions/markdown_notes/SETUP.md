# Setup Instructions for Firebase Cloud Functions

## Step 1: Install Google Cloud SDK

### macOS (using Homebrew - recommended):
```bash
brew install --cask google-cloud-sdk
```

### Or download directly:
Visit: https://cloud.google.com/sdk/docs/install

After installation, restart your terminal.

## Step 2: Authenticate and Configure

Run these commands in order:

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project genesis-melodies

# Enable required services
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

**Note:** You'll need to set up billing if you haven't already. You mentioned having Education Credits - make sure billing is enabled in the Google Cloud Console.

## Step 3: Verify Setup

Check that everything is configured:
```bash
gcloud config list
gcloud projects describe genesis-melodies
```

## Step 4: Prepare Your Flask Code

1. Copy your existing Flask server code into `functions/main.py`
2. Adapt it to the Cloud Function format (see the template in `functions/main.py`)
3. Update `functions/requirements.txt` with all your dependencies

## Step 5: Test Locally (Optional)

Install Functions Framework:
```bash
pip install functions-framework
cd functions
functions-framework --target=search --port=8080
```

Test with:
```bash
curl "http://localhost:8080?model_name=hebrew_st&record_level=verse&top_k=10&search_verses=%5B%5B12%2C1%5D%5D"
```

## Step 6: Deploy

From the project root:
```bash
gcloud functions deploy search \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./functions \
  --entry-point=search \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=300s \
  --max-instances=3 \
  --min-instances=0 \
  --set-env-vars HF_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE
```

## Step 7: Deploy Firebase Hosting

After the function is deployed, deploy your hosting:
```bash
firebase deploy --only hosting
```

The `/api/search` endpoint will automatically route to your Cloud Function via the rewrite rules in `firebase.json`.

## Troubleshooting

- **Billing errors**: Make sure billing is enabled in Google Cloud Console
- **Permission errors**: Make sure you're authenticated and have the right IAM roles
- **Deployment errors**: Check Cloud Functions logs: `gcloud functions logs read search --gen2 --region=us-central1`

