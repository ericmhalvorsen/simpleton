#!/bin/bash
# test-api.sh - Test llama.cpp API with various requests
#
# This script tests the llama.cpp API to verify multi-GPU setup is working
#
# Usage:
#   ./scripts/test-api.sh

set -e

API_URL="http://localhost:8080"

echo "========================================"
echo "llama.cpp API Test Suite"
echo "========================================"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
if curl -s "${API_URL}/health" | grep -q "ok"; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi
echo ""

# Test 2: Model info
echo "Test 2: Model Information"
echo "-------------------------"
MODEL_INFO=$(curl -s "${API_URL}/v1/models")
echo "$MODEL_INFO" | python3 -m json.tool 2>/dev/null || echo "$MODEL_INFO"
echo ""

# Test 3: Simple completion
echo "Test 3: Text Completion"
echo "-----------------------"
echo "Prompt: 'Once upon a time'"
COMPLETION=$(curl -s "${API_URL}/v1/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Once upon a time",
        "max_tokens": 50,
        "temperature": 0.7
    }')
echo "$COMPLETION" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['text'])" 2>/dev/null || echo "$COMPLETION"
echo ""

# Test 4: Chat completion
echo "Test 4: Chat Completion"
echo "-----------------------"
echo "Message: 'What is 2+2?'"
CHAT=$(curl -s "${API_URL}/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "messages": [
            {"role": "user", "content": "What is 2+2? Answer briefly."}
        ],
        "max_tokens": 50,
        "temperature": 0.3
    }')
echo "$CHAT" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "$CHAT"
echo ""

# Test 5: Performance test
echo "Test 5: Performance Test"
echo "------------------------"
echo "Generating 100 tokens..."
START_TIME=$(date +%s%N)
curl -s "${API_URL}/v1/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Write a short story about a robot:",
        "max_tokens": 100,
        "temperature": 0.7
    }' > /dev/null
END_TIME=$(date +%s%N)
ELAPSED=$((($END_TIME - $START_TIME) / 1000000))
TOKENS_PER_SEC=$(echo "scale=2; 100000 / $ELAPSED" | bc)
echo "Time: ${ELAPSED}ms"
echo "Speed: ~${TOKENS_PER_SEC} tokens/sec"
echo ""

echo "========================================"
echo "All tests completed!"
echo "========================================"
echo ""
echo "Monitor GPU usage with:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "View detailed logs:"
echo "  docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp"
