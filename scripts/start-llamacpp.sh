#!/bin/bash
# start-llamacpp.sh - Start llama.cpp server with multi-GPU support
#
# This script starts the llama.cpp Docker container with customizable parameters
# for multi-GPU inference using split mode.
#
# Usage:
#   ./scripts/start-llamacpp.sh [model_name] [gpu_count] [context_size]
#
# Examples:
#   ./scripts/start-llamacpp.sh llama-2-70b 4 4096
#   ./scripts/start-llamacpp.sh mixtral-8x7b 2 8192

set -e

# Default values
MODEL_NAME=${1:-"model"}
GPU_COUNT=${2:-4}
CTX_SIZE=${3:-4096}
BATCH_SIZE=${4:-512}

# Derived values
MODEL_PATH="/app/models/${MODEL_NAME}.gguf"
TENSOR_SPLIT=$(printf '1,%.0s' $(seq 1 $GPU_COUNT) | sed 's/,$//')
GPU_DEVICES=$(seq -s, 0 $((GPU_COUNT-1)))

echo "========================================"
echo "llama.cpp Multi-GPU Startup"
echo "========================================"
echo "Model: $MODEL_PATH"
echo "GPUs: $GPU_COUNT (devices: $GPU_DEVICES)"
echo "Tensor Split: $TENSOR_SPLIT"
echo "Context Size: $CTX_SIZE tokens"
echo "Batch Size: $BATCH_SIZE"
echo "========================================"

# Check if model file exists
if [ ! -f "models/${MODEL_NAME}.gguf" ]; then
    echo "ERROR: Model file not found: models/${MODEL_NAME}.gguf"
    echo ""
    echo "Please download a GGUF model first:"
    echo "  mkdir -p models"
    echo "  cd models"
    echo "  wget <model-url> -O ${MODEL_NAME}.gguf"
    exit 1
fi

# Stop any existing container
echo "Stopping existing containers..."
docker-compose -f docker-compose.llamacpp.yml down llamacpp 2>/dev/null || true

# Update docker-compose with custom parameters
export CUDA_VISIBLE_DEVICES="$GPU_DEVICES"
export MODEL_PATH="$MODEL_PATH"
export TENSOR_SPLIT="$TENSOR_SPLIT"
export CTX_SIZE="$CTX_SIZE"
export BATCH_SIZE="$BATCH_SIZE"

# Start the container
echo ""
echo "Starting llama.cpp server..."
docker-compose -f docker-compose.llamacpp.yml up -d llamacpp

# Wait for server to be ready
echo ""
echo "Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✓ Server is ready!"
        echo ""
        echo "API endpoint: http://localhost:8080"
        echo "View logs: docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp"
        echo "Stop server: docker-compose -f docker-compose.llamacpp.yml down llamacpp"
        echo ""
        echo "Test with:"
        echo "  curl http://localhost:8080/v1/models"
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "ERROR: Server failed to start within 60 seconds"
echo "Check logs with: docker-compose -f docker-compose.llamacpp.yml logs llamacpp"
exit 1
