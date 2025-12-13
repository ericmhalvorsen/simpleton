# Multi-GPU llama.cpp Quick Start

**TL;DR**: Run large language models across multiple GPUs using llama.cpp's split mode.

## What You Get

- ✅ **Tensor parallelism** - Distribute model layers across GPUs
- ✅ **Larger models** - Run 70B+ models that don't fit on single GPU
- ✅ **OpenAI-compatible API** - Drop-in replacement for your existing code
- ✅ **Production-ready** - Docker-based setup with monitoring tools

---

## Prerequisites

```bash
# Verify GPUs are detected
nvidia-smi

# Should show all your GPUs with CUDA support
```

---

## 5-Minute Setup

### 1. Download a Model

```bash
# For 2x 24GB GPUs - Llama 2 70B (Q4 quantized, ~40GB)
./scripts/download-model.sh \
  "https://huggingface.co/TheBloke/Llama-2-70B-GGUF/resolve/main/llama-2-70b.Q4_K_M.gguf" \
  llama-2-70b
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.llamacpp .env

# Edit for your GPU count
# For 2 GPUs: CUDA_VISIBLE_DEVICES=0,1 and TENSOR_SPLIT=1,1
# For 4 GPUs: CUDA_VISIBLE_DEVICES=0,1,2,3 and TENSOR_SPLIT=1,1,1,1
nano .env
```

### 3. Start Server

```bash
# Option A: Using helper script
./scripts/start-llamacpp.sh llama-2-70b 2 4096

# Option B: Using docker-compose directly
docker-compose -f docker-compose.llamacpp.yml build llamacpp
docker-compose -f docker-compose.llamacpp.yml up -d llamacpp
```

### 4. Test API

```bash
# Run test suite
./scripts/test-api.sh

# Or manual test
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Once upon a time", "max_tokens": 50}'
```

---

## Key Concepts

### Split Mode

**What it is**: Distributes weight matrices row-wise across GPUs (tensor parallelism)

**Why it matters**: Allows models larger than single GPU VRAM to run efficiently

**Configuration**:
```bash
--split-mode row        # Use tensor parallelism
--tensor-split 1,1,1,1  # Equal split across 4 GPUs
```

### Tensor Split Ratios

Controls how much of the model goes on each GPU:

| Config | Meaning |
|--------|---------|
| `1,1` | 50% on each GPU (2 GPUs) |
| `1,1,1,1` | 25% on each GPU (4 GPUs) |
| `2,1,1,1` | 40% on GPU 0, 20% on others |
| `1,1,0,0` | Use only first 2 GPUs |

**Rule**: Ratios are relative (sum doesn't need to be 100)

### Context Size

Maximum conversation length in tokens:

- **2048**: Short conversations, low VRAM (~40GB for 70B Q4)
- **4096**: Standard use case (~45GB for 70B Q4)
- **8192**: Long documents (~55GB for 70B Q4)
- **32768**: Very long context (~100GB+ for 70B Q4)

**Trade-off**: Larger context = more VRAM used

---

## Common Commands

```bash
# Start server
docker-compose -f docker-compose.llamacpp.yml up -d llamacpp

# View logs
docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp

# Stop server
docker-compose -f docker-compose.llamacpp.yml down llamacpp

# Monitor GPU usage
./scripts/monitor-gpus.sh

# Test API
./scripts/test-api.sh
```

---

## File Reference

| File | Purpose |
|------|---------|
| `Dockerfile.llamacpp` | Builds llama.cpp with CUDA |
| `docker-compose.llamacpp.yml` | Multi-GPU service config |
| `.env.llamacpp` | Environment variables template |
| `MULTI_GPU_SETUP.md` | **Comprehensive documentation** ← Read this for details |
| `scripts/start-llamacpp.sh` | Easy startup script |
| `scripts/monitor-gpus.sh` | Real-time GPU monitoring |
| `scripts/test-api.sh` | API test suite |
| `scripts/download-model.sh` | Model download helper |
| `scripts/example_llamacpp_client.py` | Python API client example |

---

## Troubleshooting

### Issue: Out of Memory

**Solutions**:
- Reduce context: Change `CTX_SIZE=2048` in `.env`
- Use smaller model: Q4 instead of Q6/Q8
- Reduce batch size: Add `--batch-size 256` to command

### Issue: Slow Inference (>500ms/token)

**Possible causes**:
1. **No NVLink**: Check with `nvidia-smi topo -m`
   - Look for "NV" connections (fast)
   - "SYS" means PCIe (slower)
2. **Unbalanced split**: Use equal ratios like `1,1,1,1`
3. **CPU bottleneck**: Increase `THREADS` in `.env`

### Issue: GPUs Not Detected

**Solutions**:
1. Verify Docker GPU access:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
   ```
2. Check `CUDA_VISIBLE_DEVICES` in `.env`
3. Ensure NVIDIA Container Toolkit installed

---

## Model Recommendations

| GPU Setup | Total VRAM | Recommended Model | Quantization |
|-----------|------------|-------------------|--------------|
| 2x 24GB | 48GB | Llama 2/3 70B | Q4_K_M |
| 2x 24GB | 48GB | Mixtral 8x7B | Q5_K_M |
| 4x 24GB | 96GB | Llama 3 70B | Q8_0 |
| 4x 24GB | 96GB | Qwen2.5 72B | Q6_K |
| 8x 24GB | 192GB | Llama 3.1 405B | Q4_0 |

**Quantization guide**:
- **Q4**: Smallest, fastest, lower quality
- **Q5**: Balanced quality/size
- **Q6**: High quality, larger size
- **Q8**: Near-original quality, largest size

---

## API Examples

### Python

```python
import httpx

async def generate(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/v1/completions",
            json={"prompt": prompt, "max_tokens": 100}
        )
        return response.json()["choices"][0]["text"]
```

### curl

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8080/v1/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Once upon a time',
    max_tokens: 100
  })
});
const data = await response.json();
console.log(data.choices[0].text);
```

---

## Performance Tips

1. **Enable NVLink** if available (check with `nvidia-smi topo -m`)
2. **Use equal tensor splits** for balanced load (`1,1,1,1`)
3. **Start with Q4 quantization** for best speed/quality trade-off
4. **Monitor GPU usage** with `./scripts/monitor-gpus.sh`
5. **Tune batch size** based on your VRAM headroom

---

## Next Steps

1. ✅ Read [MULTI_GPU_SETUP.md](./MULTI_GPU_SETUP.md) for comprehensive documentation
2. ✅ Try different models with `./scripts/download-model.sh`
3. ✅ Experiment with `--tensor-split` ratios
4. ✅ Integrate API into your application using `scripts/example_llamacpp_client.py`
5. ✅ Monitor performance and tune parameters

---

## Getting Help

- **Detailed docs**: See [MULTI_GPU_SETUP.md](./MULTI_GPU_SETUP.md)
- **llama.cpp GitHub**: https://github.com/ggerganov/llama.cpp
- **Check logs**: `docker-compose -f docker-compose.llamacpp.yml logs -f llamacpp`
- **GPU monitor**: `./scripts/monitor-gpus.sh`
