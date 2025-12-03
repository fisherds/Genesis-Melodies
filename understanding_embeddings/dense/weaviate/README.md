# Weaviate Migration - Lessons Learned

## Summary

This folder contains our experiment with migrating from ChromaDB to Weaviate and creating a TypeScript backend. **This approach has been abandoned** in favor of a Python-only backend.

## What Worked

### ✅ Weaviate Upsert (`upsert/upsert_collections.py`)
- Successfully upserted all 5 original collections to Weaviate
- Manual vectorization approach works well
- Weaviate Cloud integration is solid
- The upsert script is production-ready

## What Didn't Work

### ❌ TypeScript Backend (`backend/`)

**Problems Encountered:**

1. **ONNX Model Limitations**
   - `@xenova/transformers` requires ONNX model format
   - English ST model (`sentence-transformers/all-mpnet-base-v2`) has ONNX version ✅
   - Hebrew ST model (`odunola/sentence-transformers-bible-reference-final`) - **NO ONNX version** ❌
   - BERiT model (`gngpostalsrvc/BERiT`) - **NO ONNX version** ❌

2. **Hybrid Approach Complexity**
   - Attempted Python fallback for Hebrew models
   - Breaks the "isolated backend" goal
   - Adds deployment complexity (need Python + Node.js)
   - Not suitable for Firebase Cloud Functions (TypeScript runtime)

3. **Model Conversion Challenges**
   - Converting models to ONNX is non-trivial
   - Requires additional tooling (Optimum)
   - May not preserve exact model behavior
   - One-time conversion doesn't solve ongoing maintenance

4. **TypeScript/Weaviate Client Issues**
   - Type definitions incomplete
   - API differences between versions
   - Required workarounds and type assertions

## Decision: Python-Only Backend

**Why Python?**

1. ✅ **All models work natively** - No conversion needed
2. ✅ **Existing codebase** - Flask server already works
3. ✅ **Firebase Cloud Functions** - Python runtime is well-supported
4. ✅ **Simpler deployment** - Single language, single runtime
5. ✅ **Better ML ecosystem** - Transformers, PyTorch, etc. all Python-native

## Next Steps: Choose Vector Database

### Option A: Python Backend + Weaviate

**Pros:**
- ✅ Weaviate Cloud (managed, scalable)
- ✅ Already have upsert script working
- ✅ Better for production scale
- ✅ Hybrid search (vector + BM25) built-in
- ✅ Multi-tenancy support

**Cons:**
- ❌ Additional service dependency
- ❌ Cost (Weaviate Cloud pricing)
- ❌ Need to maintain Weaviate collections
- ❌ More complex than needed for MVP

**Best for:** Production deployment, scaling to many users, need for hybrid search

### Option B: Python Backend + ChromaDB

**Pros:**
- ✅ Already working (existing Flask server)
- ✅ No additional service dependency
- ✅ Free (self-hosted)
- ✅ Simpler deployment
- ✅ Faster to implement (code already exists)

**Cons:**
- ❌ Self-hosted (need to manage)
- ❌ Less scalable than Weaviate
- ❌ No built-in hybrid search
- ❌ File-based storage (backup considerations)

**Best for:** MVP, demo site, simpler deployment, cost-sensitive

## Recommendation: ChromaDB for MVP

**Decision: Use ChromaDB (Option B) for public demo**

### Why ChromaDB?

1. ✅ **Already Working**
   - Flask server (`flask_server/app.py`) already uses ChromaDB
   - All endpoints functional (`/api/search`)
   - All models work (BERiT, Hebrew ST, English ST)
   - All record levels supported (pericope, verse, agentic)

2. ✅ **Faster Deployment**
   - No additional service setup
   - No Weaviate Cloud account needed
   - ChromaDB files can be bundled with deployment
   - Simpler Firebase Cloud Functions setup

3. ✅ **Cost Effective**
   - Free (self-hosted)
   - No per-query costs
   - No monthly service fees

4. ✅ **Sufficient for MVP**
   - Handles demo traffic easily
   - File-based storage is fine for initial scale
   - Can migrate to Weaviate later if needed

5. ✅ **Migration Path Available**
   - Upsert script ready (`upsert/upsert_collections.py`)
   - Weaviate collections already created
   - Can switch to Weaviate when scale requires it

### When to Consider Weaviate

Switch to Weaviate if:
- Traffic exceeds ChromaDB file-based limits
- Need hybrid search (vector + BM25)
- Need multi-tenancy
- Want managed service (less ops overhead)
- Scaling to production with many concurrent users

### Current Flask Server Status

✅ **Ready for Deployment:**
- `/api/search` endpoint works
- All 3 models supported
- All 5 record levels (pericope, verse, 3 agentic)
- Frontend fully functional
- Verse lookup working
- Bible reader integrated

**What's Needed:**
- Deploy to Firebase Cloud Functions (Python runtime)
- Bundle ChromaDB files with deployment
- Configure environment variables
- Set up Firebase Hosting for static files

## What to Keep

- ✅ `upsert/upsert_collections.py` - Keep for future Weaviate migration
- ✅ Weaviate collections (already created) - Keep for future use
- ❌ `backend/` folder - Can be deleted or archived

## Next Steps: Deploy Flask Server to Firebase

### Current State
- ✅ Flask server working with ChromaDB
- ✅ All models and record levels supported
- ✅ Frontend complete
- ✅ API endpoints functional

### Deployment Plan

1. **Firebase Cloud Functions Setup**
   - Use Python 3.11 runtime
   - Convert Flask app to Cloud Function
   - Bundle ChromaDB vector stores
   - Include data files (WLCa.json, bp_translation, verse_lookup.json)

2. **Firebase Hosting**
   - Serve static files (HTML, CSS, JS)
   - Proxy API calls to Cloud Functions

3. **Configuration**
   - Environment variables for paths
   - ChromaDB persistence directory
   - Model loading configuration

### Files to Deploy

**Backend (Cloud Functions):**
- `flask_server/app.py` - Main Flask app
- `dense/vector_store.py` - ChromaDB loading
- `dense/search.py` - Search logic
- `dense/models.py` - Embedding models
- `shared/` - Utilities
- `data/records/` - Record JSON files
- `data/raw/` - WLCa.json, bp_translation
- `dense/chroma_db/` - Vector stores (all 12 collections)

**Frontend (Firebase Hosting):**
- `flask_server/public/` - All static files

### Estimated Deployment Size
- ChromaDB files: ~50-100 MB (all collections)
- Data files: ~10-20 MB
- Python dependencies: ~500 MB (models cached)
- **Total: ~600-700 MB** (within Cloud Functions limits)

## Conclusion

The TypeScript backend experiment taught us:
- Not all models have ONNX versions
- Hybrid approaches add complexity
- Python is the right tool for ML backends
- ChromaDB is sufficient for MVP/demo purposes

**Next:** Proceed with Python Flask backend + ChromaDB for public demo.

