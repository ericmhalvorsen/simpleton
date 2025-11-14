# Frontend Setup Guide

## Overview

This project now includes a modern web frontend built with **SvelteKit** and **Bun** for managing chats and interacting with the Simpleton LLM backend.

## Architecture

```
Simpleton (Multi-Repo Setup)
├── Backend (FastAPI)
│   ├── LLM Inference (Ollama)
│   ├── RAG (Qdrant)
│   ├── Caching (Redis)
│   └── Notifications (ntfy)
└── Frontend (SvelteKit + Bun)
    ├── Chat Interface
    ├── Message Management
    └── Model Selection
```

## Quick Start

### 1. Start the Backend

```bash
# From the root directory
docker-compose up -d

# Or using mise
mise run start
```

The backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 2. Start the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Run the development script (with hot reload)
./dev.sh

# Or manually
bun install
bun run dev
```

The frontend will be available at:
- App: http://localhost:5173

## Features

### Hot Module Reloading (HMR) ⚡

The frontend includes **hot module reloading** powered by Vite:

- **Instant Updates**: Changes to Svelte components reflect immediately
- **State Preservation**: Component state is maintained during updates
- **Error Overlay**: Build errors appear in-browser for quick debugging
- **Fast Refresh**: Full HMR for `.svelte`, `.ts`, and `.css` files

### Chat Management

- **Multiple Chats**: Create and manage multiple chat sessions
- **Persistent Storage**: Chats saved to browser localStorage
- **Auto-Naming**: Chats automatically titled from first message
- **Chat History**: View and search through past conversations

### Real-Time Messaging

- **Streaming Responses**: LLM responses stream in real-time
- **Auto-Scroll**: Messages automatically scroll to bottom
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Clear error messages for failed requests

### Modern UI

- **Dark Theme**: Easy on the eyes dark mode interface
- **Responsive**: Works on desktop and mobile
- **Smooth Animations**: Polished user experience
- **Accessible**: Keyboard shortcuts and semantic HTML

## Configuration

### Environment Variables

Create `frontend/.env`:

```env
# Backend API URL (default: http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000

# API Key from backend .env
VITE_API_KEY=your-api-key-here
```

### API Key Setup

1. Check your backend API key:
   ```bash
   cat .env | grep API_KEYS
   ```

2. Copy one of the keys to `frontend/.env`:
   ```env
   VITE_API_KEY=your-key-from-backend
   ```

## Development Workflow

### Making Changes

1. **Edit Components**: Modify files in `frontend/src/lib/components/`
2. **See Changes Instantly**: HMR updates the browser automatically
3. **Check Browser**: Changes appear without refresh

### Common Development Tasks

```bash
# Start dev server with HMR
bun run dev

# Type checking
bun run check

# Type checking in watch mode
bun run check:watch

# Build for production
bun run build

# Preview production build
bun run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts        # API client with streaming support
│   │   │   └── types.ts         # TypeScript type definitions
│   │   ├── components/
│   │   │   ├── ChatSidebar.svelte    # Sidebar with chat list
│   │   │   ├── ChatWindow.svelte     # Main chat interface
│   │   │   ├── ChatMessage.svelte    # Individual message display
│   │   │   └── ChatInput.svelte      # Message input with auto-resize
│   │   └── stores/
│   │       └── chats.ts         # Svelte stores for state
│   ├── routes/
│   │   ├── +page.svelte         # Main page
│   │   └── +layout.svelte       # App layout
│   ├── app.html                 # HTML template
│   ├── app.css                  # Global styles
│   └── app.d.ts                 # Type declarations
├── static/                       # Static assets
├── .env                         # Environment variables
├── package.json                 # Dependencies
├── vite.config.ts               # Vite configuration (HMR settings)
├── svelte.config.js             # SvelteKit configuration
├── tsconfig.json                # TypeScript configuration
├── dev.sh                       # Development startup script
└── README.md                    # Frontend documentation
```

## Technology Stack

| Technology | Purpose | Why? |
|------------|---------|------|
| **SvelteKit** | Frontend framework | Fast, reactive, less boilerplate |
| **Bun** | Runtime & package manager | 10-100x faster than npm, built-in bundler |
| **Vite** | Build tool | Lightning-fast HMR, optimized builds |
| **TypeScript** | Type safety | Catch errors at compile time |
| **LocalStorage** | State persistence | Simple, fast, client-side storage |

## API Integration

The frontend communicates with the backend via REST API:

### Chat Endpoint

```typescript
// Send a chat message with streaming
for await (const chunk of apiClient.chatStream({
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
  model: 'qwen2.5:7b',
  temperature: 0.7
})) {
  console.log(chunk); // Each chunk of the response
}
```

### Available Models

```typescript
// Get list of available models
const models = await apiClient.getModels();
```

### Health Check

```typescript
// Check if backend is running
const health = await apiClient.healthCheck();
```

## Troubleshooting

### Backend Connection Failed

**Problem**: "Backend is offline" banner appears

**Solution**:
1. Ensure backend is running:
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

2. Check API key matches:
   ```bash
   # Backend
   cat .env | grep API_KEYS

   # Frontend
   cat frontend/.env | grep VITE_API_KEY
   ```

3. Verify CORS is enabled in `app/main.py`

### Hot Reload Not Working

**Problem**: Changes don't appear automatically

**Solution**:
1. Check dev server is running on port 5173
2. Clear browser cache (Ctrl+Shift+R)
3. Check terminal for Vite errors
4. Restart dev server:
   ```bash
   cd frontend
   bun run dev
   ```

### TypeScript Errors

**Problem**: Type errors in components

**Solution**:
1. Run type checking:
   ```bash
   bun run check
   ```

2. Check type definitions in `src/lib/api/types.ts`

3. Ensure `@types` packages are installed

### Streaming Not Working

**Problem**: Messages don't stream, appear all at once

**Solution**:
1. Check browser console for errors
2. Verify backend supports streaming (should by default)
3. Check network tab shows `Transfer-Encoding: chunked`

## Production Deployment

### Build

```bash
cd frontend
bun run build
```

Output will be in `frontend/build/`.

### Serve

Use any static file server:

```bash
# Using Bun
cd build
bun run ../node_modules/.bin/vite preview

# Using Node.js
npx serve build

# Using Python
cd build
python -m http.server 4173
```

### Environment Variables

For production, set:

```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_API_KEY=your-production-api-key
```

## Next Steps

### Potential Enhancements

1. **Model Switcher**: Add UI to change models per chat
2. **RAG Integration**: Add document upload and RAG queries
3. **Settings Page**: Configure API URL, theme, etc.
4. **Export Chats**: Download chat history as JSON/Markdown
5. **Image Upload**: Support vision endpoint
6. **Audio Input**: Support audio transcription
7. **Multi-User**: Add authentication and user accounts
8. **Themes**: Light mode and custom color schemes

### Contributing

1. Make changes in a feature branch
2. Test with `bun run check`
3. Build with `bun run build`
4. Test production build with `bun run preview`
5. Submit pull request

## Resources

- [SvelteKit Documentation](https://kit.svelte.dev/)
- [Bun Documentation](https://bun.sh/docs)
- [Vite Documentation](https://vitejs.dev/)
- [Svelte Documentation](https://svelte.dev/)
- [Backend API Docs](http://localhost:8000/docs)

## Support

For issues or questions:
1. Check backend logs: `docker-compose logs -f`
2. Check frontend console in browser DevTools
3. Review this documentation
4. Check the main [README.md](../README.md)
