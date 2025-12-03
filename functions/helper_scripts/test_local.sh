#!/bin/bash
# Quick test script for local Cloud Function testing
# Note: This script uses the venv from project root (same as start_test.sh)
# For consistency, prefer using start_test.sh instead

cd "$(dirname "$0")/../.."

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run ./functions/helper_scripts/setup_venv.sh first"
    exit 1
fi

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "🧪 Starting Cloud Function locally..."
echo "📡 Server will be available at: http://localhost:8080"
echo ""
echo "📝 Test with:"
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

