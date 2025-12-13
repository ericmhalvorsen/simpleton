# llama.cpp vs vLLM Quick Comparison

## When to Use What

| Use Case | Choose |
|----------|--------|
| Single user / personal use | **llama.cpp** |
| 10-100+ concurrent users | **vLLM** |
| Intel Arc GPU | **llama.cpp** (vLLM doesn't support) |
| NVIDIA GPUs only | Either, **vLLM** for high throughput |
| CPU-only inference | **llama.cpp** |
| Maximum throughput | **vLLM** |
| Maximum compatibility | **llama.cpp** |

## Quick Start Commands

### llama.cpp
```bash
# Download model (GGUF format)
./scripts/download-model.sh <url> llama-2-70b

# Start with 2 GPUs
./scripts/start-llamacpp.sh llama-2-70b 2 4096

# Test
./scripts/test-api.sh
```

### vLLM
```bash
# Start with HuggingFace model, 4 GPUs
./scripts/start-vllm.sh meta-llama/Llama-2-70b-chat-hf 4 4096 256

# Test
./scripts/test-vllm.sh
```

## Key Differences

### llama.cpp
- **Port**: 8080
- **Format**: GGUF models (quantized)
- **Setup**: Manual tensor splits `--tensor-split 1,1,1,1`
- **GPUs**: NVIDIA, AMD, Intel, Apple Silicon
- **Best for**: Single user, varied hardware

### vLLM
- **Port**: 8000
- **Format**: HuggingFace models (native)
- **Setup**: Auto tensor parallel `--tensor-parallel-size 4`
- **GPUs**: NVIDIA only (CUDA)
- **Best for**: Multiple concurrent users

## Performance Example (70B model, 2x A100)

| Scenario | llama.cpp | vLLM |
|----------|-----------|------|
| 1 user | ~50 tok/s | ~40 tok/s |
| 10 users | ~15 tok/s each | ~35 tok/s each |
| 50 users | ~5 tok/s each | ~30 tok/s each |

**vLLM wins** at high concurrency due to PagedAttention and continuous batching.

## Configuration Files

| File | llama.cpp | vLLM |
|------|-----------|------|
| Dockerfile | `Dockerfile.llamacpp` | `Dockerfile.vllm` |
| Compose | `docker-compose.llamacpp.yml` | `docker-compose.vllm.yml` |
| Env | `.env.llamacpp` | `.env.vllm` |
| Start Script | `scripts/start-llamacpp.sh` | `scripts/start-vllm.sh` |
| Test Script | `scripts/test-api.sh` | `scripts/test-vllm.sh` |

## Intel Arc Note

**vLLM does NOT support Intel Arc GPUs** - it's NVIDIA CUDA only.

If you have Intel Arc + NVIDIA:
- vLLM will use only NVIDIA GPUs
- llama.cpp can use Intel Arc GPUs (set `DEVICE=Arc` in original Ollama setup)

## Both Use Same API

Both expose OpenAI-compatible endpoints:
- `/v1/completions`
- `/v1/chat/completions`
- `/v1/models`

Switch between them without changing your application code (just change the URL).
