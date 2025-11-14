# Contributing to Simpleton

Thank you for your interest in contributing to Simpleton! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) - Python package manager
- [Bun](https://bun.sh) - For frontend development
- Git

### Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/simpleton.git
   cd simpleton
   ```

2. **Set up the backend**
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync --extra dev

   # Copy environment file
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up the frontend**
   ```bash
   cd frontend

   # Install Bun (if not already installed)
   curl -fsSL https://bun.sh/install | bash

   # Install dependencies
   bun install

   # Copy environment file
   cp .env.example .env
   # Edit .env with your API key
   ```

4. **Start development environment**
   ```bash
   # Start backend services (from root)
   docker-compose up -d

   # Start frontend dev server (from frontend/)
   cd frontend
   bun run dev
   ```

## Code Quality

### Backend (Python)

We use **Ruff** for linting and formatting Python code.

```bash
# Run linting
uv run ruff check app/

# Auto-fix issues
uv run ruff check --fix app/

# Format code
uv run ruff format app/

# Check formatting without changes
uv run ruff format --check app/
```

### Frontend (TypeScript/Svelte)

We use **ESLint** for linting and **Prettier** for formatting.

```bash
cd frontend

# Run linting
bun run lint

# Format code
bun run format

# Type checking
bun run check
```

## Testing

### Backend Tests

```bash
# Run tests with pytest
uv run pytest

# Run with coverage
uv run pytest --cov=app
```

### Frontend Tests

```bash
cd frontend

# Type checking
bun run check

# Build test
bun run build
```

## Continuous Integration

We use GitHub Actions for CI/CD. The following checks run automatically on pull requests:

### Backend CI (`backend-ci.yml`)
- ✅ Ruff linting
- ✅ Ruff formatting check
- ⏳ Type checking (mypy - to be added)
- ⏳ Pytest tests (to be added)

### Frontend CI (`frontend-ci.yml`)
- ✅ Prettier formatting check
- ✅ ESLint linting
- ✅ TypeScript type checking
- ✅ Production build test

### Combined CI (`ci.yml`)
- ✅ Backend linting
- ✅ Frontend linting and type checking
- ✅ Frontend build
- ✅ Docker build test

All checks must pass before merging.

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

3. **Run quality checks locally**
   ```bash
   # Backend
   uv run ruff check app/
   uv run ruff format --check app/

   # Frontend
   cd frontend
   bun run lint
   bun run check
   bun run build
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   ```

   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template
   - Wait for CI checks to pass
   - Request review

## Code Style Guidelines

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function parameters and return values
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

Example:
```python
async def process_chat_message(
    message: str,
    model: str = "qwen2.5:7b",
    temperature: float = 0.7
) -> ChatResponse:
    """
    Process a chat message and return LLM response.

    Args:
        message: User's input message
        model: LLM model to use
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        ChatResponse with generated text

    Raises:
        HTTPException: If model is unavailable
    """
    # Implementation
```

### TypeScript/Svelte

- Use TypeScript for type safety
- Prefer `const` over `let`, avoid `var`
- Use async/await over promises
- Document complex functions with JSDoc
- Use descriptive variable names

Example:
```typescript
/**
 * Stream chat messages from the API
 */
async function* streamChatResponse(
	request: ChatRequest
): AsyncGenerator<string, void, unknown> {
	const response = await fetch(url, options);
	// Implementation
}
```

### Svelte Components

- Keep components focused and reusable
- Use TypeScript in `<script lang="ts">` blocks
- Document component props
- Use semantic HTML
- Scope styles to components

Example:
```svelte
<script lang="ts">
	/** Message content to display */
	export let message: ChatMessage;

	/** Whether this is the user's message */
	export let isUser: boolean = false;
</script>

<div class="message" class:user={isUser}>
	{message.content}
</div>

<style>
	.message {
		/* Scoped styles */
	}
</style>
```

## Project Structure

```
simpleton/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
├── app/                    # Backend Python code
│   ├── routers/           # FastAPI route handlers
│   ├── utils/             # Utility functions
│   ├── config.py          # Configuration
│   └── main.py            # Application entry point
├── frontend/              # Frontend SvelteKit app
│   ├── src/
│   │   ├── lib/          # Reusable code
│   │   │   ├── api/      # API client
│   │   │   ├── components/ # Svelte components
│   │   │   └── stores/   # State management
│   │   └── routes/       # SvelteKit pages
│   ├── .eslintrc.cjs     # ESLint config
│   └── .prettierrc       # Prettier config
├── docker-compose.yml     # Docker services
├── pyproject.toml         # Python dependencies
└── README.md              # Main documentation
```

## Adding New Features

### Backend Endpoints

1. Create a new router in `app/routers/`
2. Define Pydantic models in `app/models.py`
3. Add route to `app/main.py`
4. Add tests in `tests/`
5. Update API documentation

### Frontend Components

1. Create component in `frontend/src/lib/components/`
2. Add TypeScript types in `frontend/src/lib/api/types.ts`
3. Update stores if needed in `frontend/src/lib/stores/`
4. Add to appropriate route/page
5. Update documentation

## Documentation

- Update README.md for user-facing changes
- Update CONTRIBUTING.md for developer changes
- Add JSDoc/docstrings for new functions
- Update FRONTEND_SETUP.md for frontend changes

## Getting Help

- Check existing issues and PRs
- Read the documentation
- Ask questions in issue discussions
- Join our community (if applicable)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT).

---

Thank you for contributing to Simpleton! 🎉
