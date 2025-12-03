# Deployment Notes for Cloud Functions

> **Note**: This file contains historical notes about the directory structure migration. The current structure is already set up. See [../README.md](../README.md) for current information.

## Current Directory Structure

The Cloud Function uses a flattened structure with all modules directly in the `functions/` directory:

```
functions/
├── main.py                    # Cloud Function entry point
├── requirements.txt           # Python dependencies
├── dense/                     # Vector store and embedding models
│   ├── vector_store.py
│   ├── search.py
│   ├── models.py
│   └── chroma_db/            # Vector store persist directories
├── shared/                    # Shared utilities
│   ├── utils.py
│   └── verse_parser.py
└── data/                      # Data files
    ├── raw/                   # Raw data files
    └── records/               # Generated records
```

## Path Configuration

The `main.py` file uses paths relative to the `functions/` directory:
- `BASE_DIR = functions/dense` (contains chroma_db subdirectory)
- `DATA_DIR = functions/data` (contains raw and records subdirectories)

All paths are automatically resolved based on the Cloud Function's working directory.

## Memory and Timeout Considerations

- **Memory**: Start with 512MB, but you may need more (1GB or 2GB) depending on:
  - Size of your vector stores
  - Model loading requirements
  - ChromaDB memory usage

- **Timeout**: Start with 60s, but increase if searches take longer:
  - First request (cold start) may take longer due to model loading
  - Complex searches may take time

Update the deployment command:
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
  --timeout=300s
```

## Environment Variables (Optional)

For production, you might want to use environment variables for paths:
```bash
gcloud functions deploy search \
  ... \
  --set-env-vars BASE_DIR=/path/to/dense,DATA_DIR=/path/to/data
```

## Testing the Deployed Function

After deployment, test with:
```bash
curl "https://us-central1-genesis-melodies.cloudfunctions.net/search?model_name=hebrew_st&record_level=verse&top_k=10&search_verses=%5B%7B%22chapter%22%3A12%2C%22verse%22%3A1%7D%5D"
```

Or through Firebase Hosting (after deploying hosting):
```bash
curl "https://genesis-melodies.web.app/api/search?model_name=hebrew_st&record_level=verse&top_k=10&search_verses=%5B%7B%22chapter%22%3A12%2C%22verse%22%3A1%7D%5D"
```

