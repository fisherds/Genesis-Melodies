# Deployment Guide

## Prerequisites
- ✅ gcloud CLI installed and authenticated (see [SETUP.md](./SETUP.md))
- ✅ Project set: `gcloud config set project genesis-melodies`
- ✅ Services enabled (already done)
- ✅ Code tested locally and working (see [TESTING.md](./TESTING.md))
- ✅ HuggingFace token set up (see [SETUP_HF_TOKEN.md](./SETUP_HF_TOKEN.md))

## Step 1: Deploy Cloud Function

From the project root:

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
  --set-env-vars HF_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE,WEAVIATE_URL=YOUR_WEAVIATE_URL,WEAVIATE_API_KEY=YOUR_WEAVIATE_API_KEY
```

**Note:** 
- `--entry-point=router` routes both v1.0 (`/api/search`) and v2.0 (`/api/search2`) endpoints
- `WEAVIATE_URL` and `WEAVIATE_API_KEY` are required for v2.0 functionality
- See [SETUP_WEAVIATE.md](./SETUP_WEAVIATE.md) for detailed Weaviate setup instructions

**Note:** 
- 2GB memory (required for embedding models)
- 300s timeout (first request loads models - cold start takes 30-40 seconds)
- Max 3 instances (plenty for 1-10 users)
- Min 0 instances (scales to zero when idle - NO cost when sleeping!)
- HF_TOKEN required (see SETUP_HF_TOKEN.md for setup)
- WEAVIATE_URL and WEAVIATE_API_KEY required for v2.0 (see SETUP_WEAVIATE.md for setup)
- This will take 5-10 minutes

**Watch for:**
- Service URL will be printed at the end
- Note the URL for testing

## Step 2: Test the Deployed Function

After deployment completes, test with:

```bash
curl -G "https://us-central1-genesis-melodies.cloudfunctions.net/search" \
  --data-urlencode "model_name=hebrew_st" \
  --data-urlencode "record_level=verse" \
  --data-urlencode "top_k=5" \
  --data-urlencode 'search_verses=[{"chapter":12,"verse":1}]'
```

Or use the service URL from the deployment output.

## Step 3: Deploy Firebase Hosting

Once the function is working:

```bash
firebase deploy --only hosting
```

This will:
- Deploy your static files (including avraham-dense.html)
- Set up the rewrite rules to route `/api/**` to your Cloud Function

## Step 4: Test the Full Stack

Visit: `https://genesis-melodies.web.app/avraham-dense.html`

The page should:
- Load correctly
- Make API calls to `/api/search`
- Firebase will automatically route to your Cloud Function

## Troubleshooting

### Function deployment fails
- Check billing is enabled
- Verify you have quota for Cloud Functions
- Check logs: `gcloud functions logs read search --gen2 --region=us-central1`

### Function times out
- Increase timeout: `--timeout=540s` (max 9 minutes)
- Increase memory: `--memory=4GB`

### Rewrites don't work
- Verify function is deployed: `gcloud functions list --gen2`
- Check firebase.json rewrite rules
- Verify service name matches: `search`

## Cost Considerations

**💰 PAY-PER-USE MODEL (No hourly charges when idle!)**

- ✅ **Charges ONLY when handling requests** - scales to zero when idle
- ✅ **No cost when sleeping** - you can leave it running 24/7
- ✅ **Pay per invocation + compute time** - very cheap for low usage

**Cost Breakdown:**
- Invocation: ~$0.0000004 per request
- Compute: ~$0.00000125 per 100ms (1GB memory)
- **Example: 100 searches/day = ~$0.01/day = ~$0.30/month**

**For your use case (1-10 users, few searches):**
- Estimated: **$0.10 - $3/month** depending on usage
- Even with 1000 searches/day, you're looking at ~$3/month

**Cold Start:**
- First request (cold start) may take 30-60 seconds (loading models)
- Subsequent requests should be faster (5-10 seconds)
- With `--min-instances=0` (default), you pay nothing when idle
- **You're safe to leave it running!** No hourly charges when not in use

**To completely stop costs:**
- Delete the function: `gcloud functions delete search --gen2 --region=us-central1`
- Redeploy when needed (takes 5-10 minutes)

## Next Steps After Deployment

1. Monitor function logs: `gcloud functions logs read search --gen2 --region=us-central1 --limit=50`
2. Set up error alerting in Google Cloud Console
3. Consider adding caching for frequently searched verses
4. Monitor costs in Google Cloud Console

