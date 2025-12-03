# Flask Server for Abraham Reuse Demo

## Structure

```
flask_server/
├── app.py                 # Flask application
├── public/                # Static files
│   ├── index.html        # Main HTML page
│   ├── styles/
│   │   └── style.css     # CSS styles
│   └── scripts/
│       └── script.js      # JavaScript for frontend
└── README.md             # This file
```

## Running the Server

```bash
cd understanding_embeddings/flask_server
python app.py
```

The server will run on `http://localhost:8080`

## API Endpoint

### GET `/api/search`

Performs dense semantic search.

**Query Parameters:**
- `model_name`: `hebrew_st`, `berit`, or `english`
- `record_level`: `pericope` or `verse`
- `search_verses`: JSON array of verse objects, e.g., `[{"chapter": 1, "verse": 1}]`
- `top_k`: Number of results to return (default: 10)

**Example:**
```
GET /api/search?model_name=hebrew_st&record_level=pericope&search_verses=[{"chapter":1,"verse":1}]&top_k=10
```

**Response:**
JSON array of result objects, each containing:
- `id`: Record ID
- `title`: Record title
- `text`: English text
- `hebrew`: Hebrew text
- `strongs`: Strong's numbers
- `verses`: Verse references
- `score`: Similarity score

## TODO

1. **Implement search text extraction:**
   - Create `search_verses.json` file (similar to `verse_records.json`)
   - Load search verses and extract Hebrew or English text based on `model_name`
   - Concatenate text for multiple verses

2. **Handle record_level:**
   - May need different vector stores for `pericope` vs `verse` record levels
   - Update vector store loading to account for record level

3. **CORS for Firebase deployment:**
   - Add CORS headers when deploying to Firebase
   - Or use Firebase Cloud Functions

4. **Error handling:**
   - Better validation of query parameters
   - More informative error messages

## Notes

- Currently uses GET requests (no state changes)
- For local development, CORS is not needed
- Vector stores are assumed to exist in `dense/chroma_db/{model_name}_{record_level}/`

