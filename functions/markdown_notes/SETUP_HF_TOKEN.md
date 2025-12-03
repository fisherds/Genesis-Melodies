# Setup HuggingFace Token to Fix Rate Limiting

## The Problem

All HuggingFace models are being rate limited because Cloud Functions uses shared IP addresses. This affects:
- `hebrew_st` (odunola/sentence-transformers-bible-reference-final)
- `english_st` (sentence-transformers/all-mpnet-base-v2)  
- `berit` (gngpostalsrvc/BERiT)

## Solution: Use a Free HuggingFace Token

### Step 1: Get a HuggingFace Token

1. **Create/Login to HuggingFace account** (free):
   - Go to: https://huggingface.co/join
   - Or login: https://huggingface.co/login

2. **Create a token**:
   - Go to: https://huggingface.co/settings/tokens
   - Click "New token"
   - Name it (e.g., "genesis-melodies")
   - Select "Read" access (that's all you need)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

### Step 2: Redeploy Function with Token

Once you have your token, redeploy the function with it as an environment variable:

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
  --set-env-vars HF_TOKEN=your_token_here
```

**Replace `your_token_here` with your actual token!**

### Step 3: Test

After redeployment, test with:
```bash
curl -G "https://us-central1-genesis-melodies.cloudfunctions.net/search" \
  --data-urlencode "model_name=english_st" \
  --data-urlencode "record_level=verse" \
  --data-urlencode "top_k=5" \
  --data-urlencode 'search_verses=[{"chapter":12,"verse":1}]'
```

## What Changed

The code has been updated to:
- ✅ Use `HF_TOKEN` environment variable for all models
- ✅ Works with `HuggingFaceEmbeddings` (hebrew_st, english_st)
- ✅ Works with `transformers` library (berit)

## Security Note

The token is stored as an environment variable in Cloud Functions, which is secure. It's only accessible to your function, not exposed in logs or responses.

## Alternative: Wait It Out

If you don't want to set up a token right now:
- Rate limits are usually temporary (hours to a day)
- After the first successful download, models are cached
- Subsequent requests won't hit the rate limit

But for production use, a token is recommended.

