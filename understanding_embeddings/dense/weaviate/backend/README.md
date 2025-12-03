# Weaviate Backend

TypeScript backend server for querying Weaviate vector database.

**This folder is completely isolated** - it does not depend on any other project files, making it easy to port.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file in this directory (or use the one in the project root):
```
WEAVIATE_URL=https://your-weaviate-instance.weaviate.network
WEAVIATE_API_KEY=your-api-key
PORT=8080
PROJECT_ROOT=/path/to/project/root  # Optional, defaults to relative path
```

3. Build TypeScript:
```bash
npm run build
```

4. Start the server:
```bash
npm start
```

Or for development with auto-reload:
```bash
npm run dev
```

Or with watch mode:
```bash
npm run watch
```

## Structure

- `src/server.ts` - Main Express server (TypeScript)
- `tsconfig.json` - TypeScript configuration
- `dist/` - Compiled JavaScript (generated)
- Serves static files from `../../flask_server/public` (no duplication needed!)
- API endpoint: `/api/search` - Queries Weaviate collections

## API

### GET /api/search

Query parameters:
- `model_name`: `hebrew_st`, `berit`, or `english_st`
- `record_level`: `pericope`, `verse`, `agentic_berit`, `agentic_hebrew_st`, or `agentic_english_st`
- `search_verses`: JSON array of `[{"chapter": int, "verse": int}, ...]`
- `top_k`: Number of results (default: 10)

Example:
```
GET /api/search?model_name=english_st&record_level=verse&search_verses=[{"chapter":1,"verse":1}]&top_k=5
```

## Testing

Test embedding generation:
```bash
npm run test:embeddings
```

This will test all three models (English ST, Hebrew ST, BERiT) with sample text.

## Embedding Generation

The backend uses a **hybrid approach** for embedding generation:

- **English ST**: Uses `@xenova/transformers` (ONNX models, pure TypeScript)
- **Hebrew ST & BERiT**: Uses Python fallback (these models don't have ONNX versions)

The Python fallback calls `generate_embedding_python.py` which uses the existing Python embedding functions. This ensures compatibility with all models while keeping the backend mostly self-contained.


## TODO

- [x] Implement embedding generation (hybrid: TypeScript for English, Python for Hebrew)
- [ ] Test with actual Weaviate queries
- [ ] Add error handling and validation
- [ ] Add logging
- [ ] Consider converting Hebrew models to ONNX for full TypeScript support
- [ ] Consider bundling data files or using a different approach for verse lookup

