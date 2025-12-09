#!/bin/bash
# start-vllm.sh - Start vLLM server with multi-GPU support

set -e

MODEL_NAME=${1:-"meta-llama/Llama-2-70b-chat-hf"}
GPU_COUNT=${2:-4}
MAX_LEN=${3:-4096}
MAX_SEQS=${4:-256}

echo "========================================"
echo "vLLM Multi-GPU Startup"
echo "========================================"
echo "Model: $MODEL_NAME"
echo "GPUs: $GPU_COUNT (tensor parallel)"
echo "Max Length: $MAX_LEN tokens"
echo "Max Sequences: $MAX_SEQS"
echo "========================================"

export MODEL_NAME="$MODEL_NAME"
export TENSOR_PARALLEL_SIZE="$GPU_COUNT"
export MAX_MODEL_LEN="$MAX_LEN"
export MAX_NUM_SEQS="$MAX_SEQS"

echo "Stopping existing containers..."
docker-compose -f docker-compose.vllm.yml down vllm 2>/dev/null || true

echo ""
echo "Starting vLLM server..."
docker-compose -f docker-compose.vllm.yml up -d vllm

echo ""
echo "Waiting for server to start (this may take 1-2 minutes)..."
for i in {1..60}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Server is ready!"
        echo ""
        echo "API endpoint: http://localhost:8000"
        echo "View logs: docker-compose -f docker-compose.vllm.yml logs -f vllm"
        echo ""
        echo "Test with:"
        echo "  curl http://localhost:8000/v1/models"
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "ERROR: Server failed to start"
echo "Check logs: docker-compose -f docker-compose.vllm.yml logs vllm"
exit 1
