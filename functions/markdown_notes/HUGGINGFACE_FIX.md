# HuggingFace Rate Limit Fix

## The Problem

HuggingFace rate limits anonymous model downloads. The error you're seeing:
```
429 Client Error: Too Many Requests
We had to rate limit your IP
```

This happens when:
- Downloading models without authentication
- Making too many requests from the same IP
- The model `odunola/sentence-transformers-bible-reference-final` is less popular/private

## Solutions

### Option 1: Use HuggingFace Token (Recommended)

1. **Get a free HuggingFace token:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new token (read access is enough)
   - Copy the token

2. **Set it as an environment variable in Cloud Functions:**
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

3. **Update the code to use the token:**
   The `HuggingFaceEmbeddings` class should automatically use the `HF_TOKEN` environment variable if set.

### Option 2: Wait for Rate Limit to Clear

- HuggingFace rate limits are usually temporary (hours to a day)
- After the first successful download, models are cached
- Subsequent requests won't hit the rate limit

### Option 3: Use Alternative Models

If `odunola/sentence-transformers-bible-reference-final` continues to have issues:
- Check if there's an alternative Hebrew sentence transformer model
- Or pre-download and cache the model (complex, not recommended)

## Which Models Will Work?

**✅ Should work fine:**
- `sentence-transformers/all-mpnet-base-v2` (english_st) - Very popular, well-cached
- `gngpostalsrvc/BERiT` (berit) - Public model, should work

**⚠️ May have issues:**
- `odunola/sentence-transformers-bible-reference-final` (hebrew_st) - Less popular, may need token

## Quick Test

Try using `berit` or `english_st` models first to see if they work:
```bash
curl -G "https://us-central1-genesis-melodies.cloudfunctions.net/search" \
  --data-urlencode "model_name=english_st" \
  --data-urlencode "record_level=verse" \
  --data-urlencode "top_k=5" \
  --data-urlencode 'search_verses=[{"chapter":12,"verse":1}]'
```

## Recommended Action

1. **For now:** Try `berit` or `english_st` models (they should work)
2. **For production:** Get a free HuggingFace token and redeploy with `--set-env-vars HF_TOKEN=...`
3. **Long-term:** The models will cache after first download, so this is mainly a first-time issue

