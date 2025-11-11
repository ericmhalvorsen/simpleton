.PHONY: help start stop restart logs build clean pull-models test

help:
	@echo "Simpleton LLM Service - Available Commands:"
	@echo ""
	@echo "  make start        - Start all services"
	@echo "  make stop         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View service logs"
	@echo "  make build        - Rebuild containers"
	@echo "  make clean        - Stop and remove all containers/volumes"
	@echo "  make pull-models  - Pull recommended models"
	@echo "  make test         - Run basic API tests"
	@echo ""

start:
	@echo "Starting Simpleton services..."
	docker-compose up -d
	@echo "Services started! API: http://localhost:8000/docs"

stop:
	@echo "Stopping services..."
	docker-compose down

restart:
	@echo "Restarting services..."
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f simpleton

logs-ollama:
	docker-compose logs -f ollama

build:
	@echo "Building containers..."
	docker-compose build

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup complete!"

pull-models:
	@echo "Pulling recommended models..."
	@echo "This may take a while depending on your internet connection..."
	docker exec simpleton-ollama ollama pull qwen2.5:7b
	docker exec simpleton-ollama ollama pull nomic-embed-text
	@echo "Models pulled successfully!"

list-models:
	@echo "Available models:"
	docker exec simpleton-ollama ollama list

shell-api:
	docker exec -it simpleton-api /bin/bash

shell-ollama:
	docker exec -it simpleton-ollama /bin/bash

test:
	@echo "Testing API health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"
