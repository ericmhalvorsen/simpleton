#!/bin/bash
# test-vllm.sh - Test vLLM API

set -e

API_URL="http://localhost:8000"

echo "========================================"
echo "vLLM API Test"
echo "========================================"
echo ""

echo "Test 1: Health Check"
curl -s "${API_URL}/health" && echo "✓ Passed" || echo "✗ Failed"
echo ""

echo "Test 2: Model Info"
curl -s "${API_URL}/v1/models" | python3 -m json.tool
echo ""

echo "Test 3: Completion"
curl -s "${API_URL}/v1/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "default", "prompt": "Once upon a time", "max_tokens": 50}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['text'])"
echo ""

echo "Test 4: Chat"
curl -s "${API_URL}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model": "default", "messages": [{"role": "user", "content": "What is 2+2?"}], "max_tokens": 50}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
echo ""

echo "All tests completed!"
