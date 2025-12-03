#!/bin/bash
# Start the Cloud Function locally for testing
# This script activates the venv and starts the function

cd "$(dirname "$0")/../.."

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "🚀 Starting Cloud Function locally..."
echo "📡 Server will be available at: http://localhost:8080"
echo ""
echo "📝 Test with this command (in another terminal):"
echo '   curl -G "http://localhost:8080" \'
echo '     --data-urlencode "model_name=hebrew_st" \'
echo '     --data-urlencode "record_level=verse" \'
echo '     --data-urlencode "top_k=5" \'
echo '     --data-urlencode '\''search_verses=[{"chapter":12,"verse":1}]'\'
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd functions
functions-framework --target=search --port=8080 --debug
