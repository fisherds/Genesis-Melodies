# Cloud Functions for Genesis Melodies

This directory contains the Python Cloud Function that handles search requests for dense vector embeddings and ChromaDB retrievals.

## Quick Start

1. **Setup**: See [SETUP.md](./markdown_notes/SETUP.md) for initial gcloud CLI setup
2. **Deploy**: See [DEPLOY.md](./markdown_notes/DEPLOY.md) for deployment instructions
3. **Test Locally**: See [TESTING.md](./markdown_notes/TESTING.md) for local testing guide

## Documentation Overview

This directory contains several documentation files to help you work with the Cloud Function:

### Setup & Deployment
- **[SETUP.md](./markdown_notes/SETUP.md)** - Initial setup instructions (gcloud CLI, authentication, service enablement)
- **[DEPLOY.md](./markdown_notes/DEPLOY.md)** - Complete deployment guide with current settings (2GB memory, 300s timeout, cost considerations)

### Testing & Development
- **[TESTING.md](./markdown_notes/TESTING.md)** - Local testing guide using functions-framework
- **[DEMO_PREP.md](./markdown_notes/DEMO_PREP.md)** - Guide for preparing demos (warm instances, cost optimization for 30-person demos)

### Troubleshooting
- **[SETUP_HF_TOKEN.md](./markdown_notes/SETUP_HF_TOKEN.md)** - How to set up HuggingFace token to avoid rate limiting
- **[SETUP_WEAVIATE.md](./markdown_notes/SETUP_WEAVIATE.md)** - How to set up Weaviate environment variables for v2.0 search
- **[HUGGINGFACE_FIX.md](./markdown_notes/HUGGINGFACE_FIX.md)** - Alternative troubleshooting guide for HuggingFace rate limits

### Legacy/Reference
- **[DEPLOYMENT_NOTES.md](./markdown_notes/DEPLOYMENT_NOTES.md)** - Historical notes about directory structure (mostly outdated, kept for reference)

## Helper Scripts

Helper scripts for local development are in the `helper_scripts/` folder:
- **setup_venv.sh** - Creates virtual environment and installs dependencies
- **start_test.sh** - Starts the Cloud Function locally for testing
- **test_local.sh** - Alternative quick test script

## Current Configuration

- **Memory**: 2GB (required for embedding models)
- **Timeout**: 300s (5 minutes - allows for cold start model loading)
- **Max Instances**: 3 (development) / 5 (demo)
- **Min Instances**: 0 (scales to zero when idle - no cost when sleeping)
- **Region**: us-central1

## Directory Structure

```
functions/
├── main.py                    # Cloud Function entry point
├── requirements.txt           # Python dependencies
├── markdown_notes/             # Documentation files
│   ├── SETUP.md
│   ├── DEPLOY.md
│   ├── TESTING.md
│   └── ...
├── helper_scripts/            # Helper scripts for local development
│   ├── setup_venv.sh
│   ├── start_test.sh
│   └── test_local.sh
├── dense/                     # Vector store and embedding models
│   ├── vector_store.py
│   ├── search.py
│   └── models.py
├── shared/                    # Shared utilities
│   ├── utils.py
│   └── verse_parser.py
└── data/                      # Data files and record generators
    └── decoder_ring_record_generator.py
```

## Key Features

- Dense vector embeddings using HuggingFace models
- ChromaDB vector store for semantic search
- Supports multiple embedding models (hebrew_st, english_st, berit)
- Scales to zero when idle (cost-effective)
- Handles cold starts gracefully (30-40 seconds first request)

