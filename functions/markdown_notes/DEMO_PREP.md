# Demo Preparation Guide

## Understanding Warm Instances

### How It Works
- **Cold Start**: First request takes 30-40 seconds (loading models)
- **Warm Instance**: After first request, instance stays warm for ~15 minutes
- **Shared**: All users share the same warm instance(s)
- **Concurrent**: One instance can handle multiple requests simultaneously

### For Your Demo (30 People)

**With current settings (min-instances=0):**
1. You do 1 request first → warms up (30-40 sec)
2. Instance stays warm for ~15 minutes
3. All 30 people can use it during those 15 minutes → fast responses
4. After 15 minutes idle → goes cold (next request is slow)

**Risk**: If there's a gap >15 minutes, it goes cold

## Solution: Keep It Warm for Demo

### Option 1: Set Min Instances Before Demo (Recommended)

**Before your demo (30 people, 1 hour):**
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
  --max-instances=5 \
  --min-instances=2 \
  --set-env-vars HF_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE
```

**Why 2 min / 5 max for 30 people:**
- 2 min instances = ensures 2 are always warm (handles rush at start)
- 5 max instances = plenty of headroom if everyone hits it simultaneously
- Each instance can handle multiple concurrent requests
- Cost: ~$0.30/hour (2 instances × $0.15/hour) = ~$0.30 for your demo

**After your demo:**
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

**Cost**: 
- During demo: ~$0.15/hour = $0.0025/minute
- 1-hour demo = ~$0.15
- 30-minute demo = ~$0.075

### Option 2: Pre-Warm Before Demo

1. **15 minutes before demo**: Do 1-2 test requests
2. Instance stays warm for ~15 minutes
3. Start demo immediately
4. Everyone gets fast responses
5. **Cost**: Just pay-per-request (cheapest)

**Risk**: If demo runs longer than 15 minutes, it might go cold

## Recommendations

### For Development (You + 1 Person)
- **Keep min-instances=0** (current setting)
- First person does a request → warms up
- Second person gets fast response if within 15 min
- **Cost**: Very low (~$0.30-3/month)

### For 30-Person Demo
- **Set min-instances=1** 30 minutes before demo
- This ensures it's always warm
- All 30 people get fast responses
- **Cost**: ~$0.15 for the demo hour
- **After demo**: Set back to min-instances=0

### Quick Commands

**Make it always warm (for 30-person demo):**
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
  --max-instances=5 \
  --min-instances=2 \
  --set-env-vars HF_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE
```

**Make it scale to zero (after demo):**
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

## Cost Comparison

| Scenario | Min Instances | Idle Cost/Hour | Demo Cost (1 hour) | Monthly (24/7) |
|----------|---------------|----------------|-------------------|----------------|
| Development | 0 | $0 | Pay-per-request | ~$0.30-3 |
| Demo Day (30 people) | 2 | ~$0.30 | ~$0.30 | ~$216 |
| After Demo | 0 | $0 | Pay-per-request | ~$0.30-3 |

## Best Practice for Your Demo

1. **30 minutes before**: Set min-instances=1
2. **Do 1-2 test requests** to verify it's working
3. **Run your demo** - everyone gets fast responses
4. **After demo**: Set min-instances=0 to save costs

**Total demo cost**: ~$0.15 (one hour of keeping it warm)

