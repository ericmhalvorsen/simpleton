FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Install dependencies using uv
# Copy dependency files
COPY pyproject.toml .
COPY .python-version .

# Copy application code (needed for editable install)
COPY app/ ./app/

# Install dependencies in the system Python (no venv in container)
RUN uv pip install --system -e .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
