# Quick Start Guide

Get Simpleton running in 5 minutes!

## Step 1: Start the Service

```bash
# Using mise (recommended)
mise run start

# Or using the script directly
./start.sh
```

## Step 2: Configure Your API Key

1. Generate a secure API key:
```bash
openssl rand -hex 32
```

2. Edit `.env` and add your key:
```bash
API_KEYS=your-generated-key-here
```

3. Restart the service:
```bash
mise run restart
```

## Step 3: Pull Models

Pull a text generation model (choose one based on your hardware):

```bash
# 8 GB VRAM - Recommended for most users
docker exec -it simpleton-ollama ollama pull qwen2.5:7b

# Alternative models
docker exec -it simpleton-ollama ollama pull llama3.1:8b
docker exec -it simpleton-ollama ollama pull mistral:7b
```

Pull an embedding model:
```bash
docker exec -it simpleton-ollama ollama pull nomic-embed-text
```

## Step 4: Test It Out

### Option A: Use the Interactive Docs

Open http://localhost:8000/docs in your browser

1. Click "Authorize" button
2. Enter your API key
3. Try the `/inference/generate` endpoint

### Option B: Use the Example Client

```bash
# Set your API key
export SIMPLETON_API_KEY=your-api-key

# Run the example client
python example_client.py
```

### Option C: Use cURL

```bash
curl -X POST http://localhost:8000/inference/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about programming",
    "temperature": 0.7
  }'
```

## Useful Commands

```bash
# View all available tasks
mise tasks

# View logs
mise run logs

# List available models
mise run list-models

# Stop the service
mise run stop

# Restart the service
mise run restart
```

## Troubleshooting

### "Could not connect to Ollama"

Wait a minute for Ollama to fully start, then try again:
```bash
docker-compose logs ollama
```

### "Model not found"

Make sure you pulled the model (Step 3 above):
```bash
docker exec simpleton-ollama ollama list
```

### "Invalid API Key"

1. Check your `.env` file has `API_KEYS` set
2. Restart the service: `mise run restart`
3. Make sure your request includes the `X-API-Key` header

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Try different models from https://ollama.com/library
- Build your own applications using the API!

## Want to Run Locally Without Docker?

For local development with maximum performance:

```bash
# Install mise (task runner)
curl https://mise.run | sh

# Install dependencies
mise run install

# Run locally (requires Ollama installed separately)
mise run run
```

See the [README.md](README.md) "Running Without Docker" section for details.

## Need Help?

Check the troubleshooting section in README.md or open an issue.
