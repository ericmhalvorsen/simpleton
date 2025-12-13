#!/bin/bash
# download-model.sh - Download GGUF models from HuggingFace
#
# This script helps download quantized GGUF models suitable for multi-GPU inference
#
# Usage:
#   ./scripts/download-model.sh <model_url> [output_name]
#
# Examples:
#   ./scripts/download-model.sh \
#     "https://huggingface.co/TheBloke/Llama-2-70B-GGUF/resolve/main/llama-2-70b.Q4_K_M.gguf" \
#     "llama-2-70b"
#
# Popular models:
#   - Llama 2 70B Q4: Good for 2x 24GB GPUs
#   - Llama 3 70B Q4: Good for 2x 24GB GPUs
#   - Mixtral 8x7B Q5: Good for 2x 24GB GPUs
#   - Llama 3.1 405B Q4: Good for 8x 24GB GPUs

set -e

MODEL_URL=$1
OUTPUT_NAME=${2:-"model"}

if [ -z "$MODEL_URL" ]; then
    echo "ERROR: Model URL required"
    echo ""
    echo "Usage: $0 <model_url> [output_name]"
    echo ""
    echo "Recommended models by GPU configuration:"
    echo ""
    echo "2x 24GB GPUs (48GB total):"
    echo "  - Llama 2 70B Q4_K_M (~40GB)"
    echo "    https://huggingface.co/TheBloke/Llama-2-70B-GGUF/resolve/main/llama-2-70b.Q4_K_M.gguf"
    echo ""
    echo "  - Mixtral 8x7B Q5_K_M (~40GB)"
    echo "    https://huggingface.co/TheBloke/Mixtral-8x7B-v0.1-GGUF/resolve/main/mixtral-8x7b-v0.1.Q5_K_M.gguf"
    echo ""
    echo "4x 24GB GPUs (96GB total):"
    echo "  - Llama 3 70B Q8_0 (~70GB)"
    echo "    https://huggingface.co/QuantFactory/Meta-Llama-3-70B-GGUF/resolve/main/Meta-Llama-3-70B.Q8_0.gguf"
    echo ""
    echo "  - Qwen2.5 72B Q6_K (~60GB)"
    echo "    https://huggingface.co/Qwen/Qwen2.5-72B-Instruct-GGUF/resolve/main/qwen2.5-72b-instruct-q6_k.gguf"
    echo ""
    echo "8x 24GB GPUs (192GB total):"
    echo "  - Llama 3.1 405B Q4_0 (~220GB with overhead, may need some CPU offload)"
    echo ""
    echo "Find more models at https://huggingface.co/models?search=gguf"
    exit 1
fi

# Create models directory
mkdir -p models
cd models

OUTPUT_FILE="${OUTPUT_NAME}.gguf"

echo "========================================"
echo "Model Download"
echo "========================================"
echo "URL: $MODEL_URL"
echo "Output: models/$OUTPUT_FILE"
echo "========================================"
echo ""

# Check if file already exists
if [ -f "$OUTPUT_FILE" ]; then
    read -p "File $OUTPUT_FILE already exists. Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Download cancelled"
        exit 0
    fi
    rm "$OUTPUT_FILE"
fi

# Download with progress bar
echo "Downloading... (this may take a while for large models)"
echo ""

if command -v wget &> /dev/null; then
    wget --progress=bar:force:noscroll -O "$OUTPUT_FILE" "$MODEL_URL"
elif command -v curl &> /dev/null; then
    curl -L --progress-bar -o "$OUTPUT_FILE" "$MODEL_URL"
else
    echo "ERROR: Neither wget nor curl found"
    echo "Please install wget or curl to download models"
    exit 1
fi

echo ""
echo "========================================"
echo "Download Complete!"
echo "========================================"

# Get file size
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo "File: $OUTPUT_FILE"
echo "Size: $FILE_SIZE"
echo ""

# Estimate VRAM requirements
FILE_SIZE_GB=$(du -b "$OUTPUT_FILE" | cut -f1 | awk '{print $1/1024/1024/1024}')
VRAM_ESTIMATE=$(echo "$FILE_SIZE_GB * 1.2" | bc | awk '{printf "%.1f", $1}')

echo "Estimated VRAM needed: ${VRAM_ESTIMATE}GB"
echo "(includes ~20% overhead for context and KV cache)"
echo ""

# Suggest GPU configuration
if (( $(echo "$VRAM_ESTIMATE < 24" | bc -l) )); then
    echo "Recommended: 1 GPU (24GB+)"
elif (( $(echo "$VRAM_ESTIMATE < 48" | bc -l) )); then
    echo "Recommended: 2 GPUs (24GB each)"
elif (( $(echo "$VRAM_ESTIMATE < 96" | bc -l) )); then
    echo "Recommended: 4 GPUs (24GB each)"
else
    echo "Recommended: 8+ GPUs or consider smaller quantization"
fi

echo ""
echo "Start server with:"
echo "  ./scripts/start-llamacpp.sh $OUTPUT_NAME 2 4096"
echo ""
echo "Or manually:"
echo "  docker-compose -f docker-compose.llamacpp.yml up -d"

cd ..
