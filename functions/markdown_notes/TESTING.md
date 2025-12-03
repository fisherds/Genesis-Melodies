# Testing the Cloud Function

## Prerequisites

1. Set up virtual environment and install dependencies:
```bash
cd functions
./helper_scripts/setup_venv.sh  # Creates .venv in project root and installs all dependencies
```

**Note**: The `setup_venv.sh` script creates the virtual environment in the project root (`.venv/`), not in the functions directory.

## Local Testing

### Option 1: Using the test script (Recommended)
```bash
cd functions
./helper_scripts/start_test.sh  # Activates venv and starts functions-framework on port 8080
```

This script will:
- Activate the virtual environment from project root
- Start the Cloud Function locally on `http://localhost:8080`
- Show you a test curl command you can use

### Option 2: Manual start
```bash
cd functions
functions-framework --target=search --port=8080 --debug
```

### Test the endpoint

In another terminal, test with:
```bash
curl "http://localhost:8080?model_name=hebrew_st&record_level=verse&top_k=5&search_verses=%5B%7B%22chapter%22%3A12%2C%22verse%22%3A1%7D%5D"
```

Or with a prettier format:
```bash
curl -G "http://localhost:8080" \
  --data-urlencode "model_name=hebrew_st" \
  --data-urlencode "record_level=verse" \
  --data-urlencode "top_k=5" \
  --data-urlencode 'search_verses=[{"chapter":12,"verse":1}]'
```

### Expected Response

You should get a JSON response like:
```json
{
  "english_search_text": "...",
  "results": [
    {
      "id": "...",
      "title": "...",
      "text": "...",
      "hebrew": "...",
      "strongs": "...",
      "verses": "...",
      "score": 0.85
    }
  ]
}
```

## Common Issues

### Import Errors
- Make sure you're running from the `functions/` directory
- Check that all Python files are in `dense/`, `shared/`, and `data/` folders
- Verify that `chroma_db/` and `data/raw/` and `data/records/` exist

### Missing Dependencies
- Run `pip3 install -r requirements.txt` again
- Some packages (like torch) are large and may take time to download

### Path Issues
- The function expects to run from the `functions/` directory
- All paths in `main.py` are relative to `functions/`

## Next Steps

Once local testing works:
1. Deploy to Cloud Functions: `gcloud functions deploy search ...`
2. Test the deployed function
3. Deploy Firebase Hosting to use the rewrite rules

