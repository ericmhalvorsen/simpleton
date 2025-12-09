# Multi-GPU llama.cpp Setup Guide

This guide explains how to set up and use llama.cpp with multiple GPUs in split mode for high-performance inference.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [Quick Start](#quick-start)
6. [Understanding Split Modes](#understanding-split-modes)
7. [Tensor Split Ratios](#tensor-split-ratios)
8. [Performance Tuning](#performance-tuning)
9. [Troubleshooting](#troubleshooting)
10. [API Usage](#api-usage)

---

## Overview

This setup uses **llama.cpp** with CUDA support to distribute large language model inference across multiple GPUs. Unlike traditional single-GPU inference, multi-GPU split mode enables:

- **Running larger models** that don't fit on a single GPU
- **Faster inference** through parallel computation
- **Better resource utilization** across multiple GPUs

### What is Split Mode?

Split mode (also called tensor parallelism) divides the model's weight matrices across multiple GPUs. Each GPU:
1. Processes a portion of each layer's computation
2. Exchanges results with other GPUs
3. Contributes to the final output

This is different from **layer parallelism**, where entire layers are placed on different GPUs.

---

## Prerequisites

### Hardware Requirements

- **Multiple NVIDIA GPUs** with CUDA support (Compute Capability 6.0+)
- **NVLink or high-bandwidth interconnect** (recommended for best performance)
- **Sufficient VRAM**: Total VRAM should exceed model size
  - Example: 70B Q4 model needs ~40GB → 2x 24GB GPUs or 4x 12GB GPUs

### Software Requirements

- Docker with NVIDIA Container Toolkit
- NVIDIA Driver 525.60.13 or newer
- Docker Compose 1.28.0 or newer

### Verify GPU Setup

```bash
# Check NVIDIA driver
nvidia-smi

# Verify Docker can access GPUs
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Application                      │
│                     (FastAPI Backend)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP Requests
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   llama-server (Port 8080)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Model Loaded in Split Mode                 │ │
│  │                                                          │ │
│  │   GPU 0        GPU 1        GPU 2        GPU 3         │ │
│  │  ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐       │ │
│  │  │ 25% │      │ 25% │      │ 25% │      │ 25% │       │ │
│  │  │ of  │◄────►│ of  │◄────►│ of  │◄────►│ of  │       │ │
│  │  │Model│      │Model│      │Model│      │Model│       │ │
│  │  └─────┘      └─────┘      └─────┘      └─────┘       │ │
│  │     ▲            ▲            ▲            ▲           │ │
│  │     └────────────┴────────────┴────────────┘           │ │
│  │              Tensor Parallelism                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Request arrives** at llama-server via HTTP
2. **Prompt is tokenized** and prepared for inference
3. **Each token generation step**:
   - Input is broadcast to all GPUs
   - Each GPU computes its portion of the attention/FFN matrices
   - Results are synchronized across GPUs (via CUDA peer-to-peer or PCIe)
   - Output is combined and returned
4. **Response is sent** back to your application

---

## Configuration

### File Structure

```
simpleton/
├── Dockerfile.llamacpp           # Builds llama.cpp with CUDA
├── docker-compose.llamacpp.yml   # Multi-GPU service configuration
├── .env.llamacpp                 # Environment variables (copy to .env)
├── models/                       # Place your GGUF models here
│   └── model.gguf
└── config/
    └── llamacpp/                 # Optional config files
```

### Key Configuration Files

#### 1. `Dockerfile.llamacpp`

**Purpose**: Builds llama.cpp from source with CUDA support

**Key Build Flags**:
- `-DLLAMA_CUDA=ON`: Enable CUDA support
- `-DLLAMA_CUDA_F16=ON`: Use FP16 for faster computation
- `-DCMAKE_CUDA_ARCHITECTURES=all`: Support all GPU architectures

**Output**:
- `llama-server`: OpenAI-compatible API server
- `llama-cli`: Command-line interface for direct model interaction
- `libllama.so`: Shared library for the llama.cpp runtime

#### 2. `docker-compose.llamacpp.yml`

**Purpose**: Orchestrates the multi-GPU llama.cpp container

**Key Sections**:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all              # Expose all GPUs to container
          capabilities: [gpu]
```
- **What it does**: Makes all NVIDIA GPUs available inside the Docker container
- **Why**: Required for CUDA to detect and use multiple GPUs

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1,2,3
```
- **What it does**: Controls which GPUs llama.cpp can see
- **Why**: Allows you to reserve certain GPUs for other tasks

```yaml
command: >
  llama-server
  --split-mode row
  --tensor-split 1,1,1,1
  --n-gpu-layers -1
```
- **`--split-mode row`**: Enable tensor parallelism (distribute weight matrices)
- **`--tensor-split 1,1,1,1`**: Equal distribution across 4 GPUs (25% each)
- **`--n-gpu-layers -1`**: Offload all layers to GPU (vs CPU)

#### 3. `.env.llamacpp`

**Purpose**: Centralized configuration for GPU and model settings

**Key Variables**:

| Variable | Description | Example |
|----------|-------------|---------|
| `CUDA_VISIBLE_DEVICES` | Which GPUs to use | `0,1,2,3` |
| `SPLIT_MODE` | How to split model | `row` (tensor) or `layer` |
| `TENSOR_SPLIT` | Distribution ratio | `1,1,1,1` (equal) or `2,1,1,1` (unequal) |
| `N_GPU_LAYERS` | GPU layer count | `-1` (all) or `40` (partial) |
| `CTX_SIZE` | Context window | `4096`, `8192`, `32768` |

---

## Quick Start

### 1. Download a Model

```bash
# Create models directory
mkdir -p models

# Download a quantized model (example: Llama 3 8B)
# Use huggingface-cli or wget
cd models
wget https://huggingface.co/TheBloke/Llama-2-70B-GGUF/resolve/main/llama-2-70b.Q4_K_M.gguf -O model.gguf
cd ..
```

**Recommended Models by GPU Configuration**:

| GPUs | Total VRAM | Recommended Models |
|------|------------|-------------------|
| 2x 24GB | 48GB | Llama-3-70B-Q4_K_M, Mixtral-8x7B-Q5_K_M |
| 4x 24GB | 96GB | Llama-3-70B-Q8_0, Qwen2.5-72B-Q6_K |
| 8x 24GB | 192GB | Llama-3.1-405B-Q4_K_M |

### 2. Configure Environment

```bash
# Copy example config
cp .env.llamacpp .env

# Edit .env to match your GPU count
# For 2 GPUs:
# CUDA_VISIBLE_DEVICES=0,1
# TENSOR_SPLIT=1,1
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose -f docker-compose.llamacpp.yml build llamacpp

# Start the service
docker-compose -f docker-compose.llamacpp.yml up -d llamacpp

# Check logs
docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8080/health

# Generate text
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Once upon a time",
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

---

## Understanding Split Modes

llama.cpp supports multiple strategies for distributing models across GPUs:

### 1. **Row Split (Tensor Parallelism)** - RECOMMENDED

**Command**: `--split-mode row`

**How it works**:
- Divides weight matrices **row-wise** across GPUs
- Each GPU computes a portion of each layer
- Results are combined after each operation

**Pros**:
- Best performance for multi-GPU inference
- Scales well with more GPUs (2-8 GPUs)
- Supports models too large for single GPU

**Cons**:
- Requires fast GPU interconnect (NVLink preferred)
- More inter-GPU communication overhead

**Use when**:
- Model doesn't fit on single GPU
- You have 2-8 GPUs with NVLink
- Inference speed is critical

**Example VRAM usage** (70B Q4 model, 40GB total):
```
4 GPUs with --tensor-split 1,1,1,1
GPU 0: ~10GB
GPU 1: ~10GB
GPU 2: ~10GB
GPU 3: ~10GB
```

### 2. **Layer Split (Layer Parallelism)**

**Command**: `--split-mode layer`

**How it works**:
- Distributes entire **layers** across GPUs
- GPU 0 processes layers 0-N
- GPU 1 processes layers N+1-M
- Data flows sequentially through GPUs

**Pros**:
- Less inter-GPU communication
- Works without NVLink (PCIe is okay)

**Cons**:
- Slower than row split
- GPUs are underutilized (sequential processing)
- Load balancing is harder

**Use when**:
- No NVLink available
- Model fits but you want to distribute for thermal reasons

### 3. **None (Single GPU)**

**Command**: `--split-mode none`

**How it works**:
- All computation on one GPU
- Other GPUs are unused

**Use when**:
- Model fits comfortably on one GPU
- Testing or debugging

---

## Tensor Split Ratios

The `--tensor-split` parameter controls how much of the model goes on each GPU.

### Syntax

```bash
--tensor-split <ratio_gpu0>,<ratio_gpu1>,<ratio_gpu2>,...
```

Ratios are relative, not absolute percentages.

### Examples

#### Equal Split (Default)

```bash
# 4 GPUs, equal distribution (25% each)
--tensor-split 1,1,1,1
```

**Result**: Each GPU handles 25% of model

**Use when**: All GPUs have same VRAM and you want balanced load

#### Unequal Split

```bash
# 4 GPUs, 40% on GPU 0, 20% on others
--tensor-split 2,1,1,1
```

**Calculation**:
- Total ratio: 2+1+1+1 = 5
- GPU 0: 2/5 = 40%
- GPU 1-3: 1/5 = 20% each

**Use when**:
- GPUs have different VRAM capacities
- One GPU is also running display/other tasks

#### Disable Specific GPUs

```bash
# Use only GPU 0 and 1, disable 2 and 3
--tensor-split 1,1,0,0
```

**Result**: Only GPUs 0 and 1 are used

**Use when**: Reserving GPUs for other workloads

### Choosing the Right Split

| Scenario | Configuration | Ratios |
|----------|---------------|--------|
| 4x identical GPUs | All equal | `1,1,1,1` |
| 3x 24GB + 1x 12GB | Proportional | `2,2,2,1` |
| 2 GPUs, one has display | More on headless GPU | `2,1` |
| Test on single GPU | Disable others | `1,0,0,0` |

---

## Performance Tuning

### 1. Batch Size

**Parameter**: `--batch-size <N>` (default: 512)

**What it does**: Number of tokens processed in parallel during prompt ingestion

**Tuning**:
- **Higher** (1024, 2048): Faster prompt processing, more VRAM
- **Lower** (256, 128): Slower prompts, less VRAM

**Recommended**:
- Start with default (512)
- Increase if you have VRAM headroom
- Decrease if you get OOM errors

### 2. Context Size

**Parameter**: `--ctx-size <N>` (default: 512)

**What it does**: Maximum conversation/document length in tokens

**Tuning**:
- **Larger** (8192, 32768): Handle longer documents, uses more VRAM
- **Smaller** (2048, 4096): Less VRAM, suitable for chat

**VRAM impact** (approximate, 70B model):
- 2048 context: ~40GB
- 4096 context: ~45GB
- 8192 context: ~55GB
- 32768 context: ~100GB+

### 3. Thread Count

**Parameter**: `--threads <N>` (default: CPU cores)

**What it does**: CPU threads for non-GPU operations (tokenization, sampling)

**Recommended**:
- Set to # of physical cores (not hyperthreads)
- Lower if running other CPU-intensive services

### 4. Flash Attention

**Parameter**: `--flash-attn` (optional, experimental)

**What it does**: Uses optimized attention algorithm for lower VRAM

**When to use**:
- Large context sizes (>8K)
- VRAM constrained
- May have compatibility issues with some models

### 5. GPU Layers

**Parameter**: `--n-gpu-layers <N>`

**What it does**: How many model layers to offload to GPU

**Values**:
- `-1`: All layers (fastest, most VRAM)
- `40`: Partial offload (hybrid CPU/GPU)
- `0`: CPU only (slowest, no VRAM)

**Use partial offload when**:
- Model barely fits in VRAM
- Want to reserve VRAM for larger context

---

## Troubleshooting

### Issue: Out of Memory (OOM)

**Symptoms**: Container crashes, CUDA OOM errors in logs

**Solutions**:
1. Reduce context size: `--ctx-size 2048`
2. Reduce batch size: `--batch-size 256`
3. Use smaller quantization (Q4 instead of Q6)
4. Reduce GPU layers: `--n-gpu-layers 30`

### Issue: Slow Inference

**Symptoms**: High latency per token (>500ms)

**Possible causes**:

1. **No NVLink**: Row split requires fast interconnect
   - **Solution**: Check `nvidia-smi topo -m` for GPU topology
   - **Workaround**: Use `--split-mode layer` or single GPU

2. **Unbalanced tensor split**:
   - **Solution**: Use equal ratios: `--tensor-split 1,1,1,1`

3. **CPU bottleneck**:
   - **Solution**: Increase threads: `--threads 16`

4. **Thermal throttling**:
   - **Solution**: Check GPU temps with `nvidia-smi`, improve cooling

### Issue: GPUs Not Detected

**Symptoms**: llama.cpp reports 0 GPUs available

**Solutions**:

1. **Verify Docker GPU access**:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
   ```

2. **Check CUDA_VISIBLE_DEVICES**:
   ```bash
   # In docker-compose.llamacpp.yml
   environment:
     - CUDA_VISIBLE_DEVICES=0,1,2,3
   ```

3. **Verify NVIDIA Container Toolkit**:
   ```bash
   nvidia-ctk --version
   ```

### Issue: Model Fails to Load

**Symptoms**: "Unable to load model" error

**Possible causes**:

1. **Wrong model path**:
   - Check `--model /app/models/model.gguf` matches your file
   - Verify file exists: `docker exec simpleton-llamacpp ls -lh /app/models/`

2. **Corrupted download**:
   - Re-download model
   - Verify checksum if available

3. **Unsupported quantization**:
   - Use GGUF format (not older GGML)
   - Stick to standard quantizations (Q4_K_M, Q5_K_M, Q8_0)

### Getting Detailed Logs

```bash
# Enable verbose logging
# In docker-compose.llamacpp.yml, add to command:
--verbose

# View real-time logs
docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp

# Check GPU utilization
watch -n 1 nvidia-smi
```

---

## API Usage

llama-server provides an OpenAI-compatible API.

### Endpoints

#### 1. Completions

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "max_tokens": 100,
    "temperature": 0.7,
    "top_p": 0.9,
    "stop": ["\n"]
  }'
```

#### 2. Chat Completions

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

#### 3. Embeddings

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The quick brown fox jumps over the lazy dog"
  }'
```

#### 4. Model Info

```bash
curl http://localhost:8080/v1/models
```

### Python Example

```python
import requests

url = "http://localhost:8080/v1/chat/completions"
headers = {"Content-Type": "application/json"}

data = {
    "messages": [
        {"role": "user", "content": "Write a haiku about GPUs"}
    ],
    "max_tokens": 50,
    "temperature": 0.8
}

response = requests.post(url, json=data, headers=headers)
print(response.json()["choices"][0]["message"]["content"])
```

### Integrating with Your App

Update your application to use the llama.cpp server:

```python
# In your FastAPI app
import httpx

class LlamaCppClient:
    def __init__(self, base_url: str = "http://llamacpp:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def generate(self, prompt: str, max_tokens: int = 100):
        response = await self.client.post(
            f"{self.base_url}/v1/completions",
            json={"prompt": prompt, "max_tokens": max_tokens}
        )
        return response.json()["choices"][0]["text"]
```

---

## Advanced Topics

### Monitoring GPU Usage

```bash
# Real-time GPU stats
watch -n 1 nvidia-smi

# GPU memory usage
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv

# Check GPU interconnect topology
nvidia-smi topo -m
```

### Switching Between Ollama and llama.cpp

```bash
# Use Ollama (original setup)
docker-compose up -d

# Use llama.cpp multi-GPU
docker-compose -f docker-compose.llamacpp.yml up -d
```

### Custom Model Loading

Create a script to load different models:

```bash
#!/bin/bash
# load-model.sh

MODEL_NAME=$1
MODEL_PATH="/app/models/${MODEL_NAME}.gguf"

docker-compose -f docker-compose.llamacpp.yml exec llamacpp \
  pkill llama-server

docker-compose -f docker-compose.llamacpp.yml exec llamacpp \
  llama-server --model "$MODEL_PATH" --split-mode row --tensor-split 1,1,1,1
```

---

## Summary

**Key takeaways**:

1. **Row split mode** (`--split-mode row`) is best for multi-GPU inference
2. **Tensor split ratios** control distribution: `1,1,1,1` for equal split
3. **Context size** dramatically affects VRAM usage
4. **NVLink** greatly improves performance for tensor parallelism
5. Use **quantized models** (Q4, Q5) to fit larger models in less VRAM

**Next steps**:

1. Download a GGUF model
2. Configure `.env` for your GPU count
3. Run `docker-compose -f docker-compose.llamacpp.yml up -d`
4. Test with the API examples
5. Monitor with `nvidia-smi` and tune parameters

For issues, check logs: `docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp`
