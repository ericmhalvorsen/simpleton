# Simpleton Frontend

Modern chat interface for Simpleton LLM service built with **SvelteKit** and **Bun**.

## Features

- 🚀 **Fast & Modern**: Built with SvelteKit and Bun for lightning-fast performance
- 💬 **Real-time Chat**: Streaming responses from LLM models
- 🎨 **Clean UI**: Dark mode interface with smooth animations
- 📦 **Local Storage**: Chats persist in browser localStorage
- 🔥 **Hot Module Reload**: Instant updates during development
- 📱 **Responsive**: Works on desktop and mobile

## Tech Stack

- **Framework**: SvelteKit 2.x
- **Runtime**: Bun 1.x
- **Build Tool**: Vite 5.x
- **Language**: TypeScript
- **Styling**: Component-scoped CSS

## Quick Start

### Prerequisites

- [Bun](https://bun.sh) 1.0 or higher
- Simpleton backend running on `http://localhost:8000`

### Installation

1. Install dependencies:

```bash
bun install
```

2. Configure environment:

```bash
cp .env.example .env
# Edit .env and set your API key
```

3. Start development server:

```bash
bun run dev
```

The app will be available at `http://localhost:5173` with hot module reloading enabled.

## Available Scripts

- `bun run dev` - Start development server with HMR
- `bun run build` - Build for production
- `bun run preview` - Preview production build
- `bun run check` - Run TypeScript and Svelte checks

## Environment Variables

Create a `.env` file in the frontend directory:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# API Key for authentication
VITE_API_KEY=your-api-key-here
```

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts      # API client
│   │   │   └── types.ts       # TypeScript types
│   │   ├── components/
│   │   │   ├── ChatSidebar.svelte
│   │   │   ├── ChatWindow.svelte
│   │   │   ├── ChatMessage.svelte
│   │   │   └── ChatInput.svelte
│   │   └── stores/
│   │       └── chats.ts       # Chat state management
│   ├── routes/
│   │   ├── +page.svelte       # Main page
│   │   └── +layout.svelte     # Layout
│   ├── app.html               # HTML template
│   ├── app.css                # Global styles
│   └── app.d.ts               # TypeScript declarations
├── static/                     # Static assets
├── .env                        # Environment variables
├── package.json
├── svelte.config.js
├── vite.config.ts
└── tsconfig.json
```

## Features

### Chat Management

- Create multiple chat sessions
- View chat history in sidebar
- Delete individual chats
- Automatic chat titling based on first message

### Message Interface

- Send messages to LLM models
- Streaming responses with loading indicators
- Error handling with user feedback
- Auto-scrolling to latest messages
- Multi-line input support

### State Management

- Svelte stores for reactive state
- LocalStorage persistence
- Chat history preserved across sessions

## Hot Module Reload (HMR)

HMR is enabled by default in development mode:

- Component changes reflect instantly
- State is preserved during updates
- No full page reloads needed

The Vite dev server is configured for optimal HMR in `vite.config.ts`:

```ts
export default defineConfig({
	server: {
		hmr: {
			overlay: true // Show errors in browser overlay
		}
	}
});
```

## Building for Production

```bash
# Build the app
bun run build

# Preview the build
bun run preview
```

The build output will be in the `build/` directory.

## API Integration

The frontend communicates with the Simpleton backend via the API client:

```typescript
import { apiClient } from '$lib/api/client';

// Send chat message
const response = await apiClient.chat({
	messages: [{ role: 'user', content: 'Hello!' }],
	model: 'qwen2.5:7b'
});

// Stream chat response
for await (const chunk of apiClient.chatStream(request)) {
	console.log(chunk);
}

// Get available models
const models = await apiClient.getModels();
```

## Troubleshooting

### Backend Connection Issues

If you see "Backend is offline" warning:

1. Ensure Simpleton backend is running:

   ```bash
   cd .. && docker-compose up -d
   ```

2. Verify backend is accessible:

   ```bash
   curl http://localhost:8000/health
   ```

3. Check API key in `.env` matches backend configuration

### CORS Errors

The backend should already have CORS enabled. If you encounter CORS issues:

1. Verify CORS middleware in `app/main.py`
2. Check browser console for specific CORS errors
3. Ensure `VITE_API_BASE_URL` in `.env` is correct

### HMR Not Working

If hot reload isn't working:

1. Check that dev server is running on correct port (5173)
2. Clear browser cache and restart dev server
3. Check Vite logs for any errors

## Development Tips

### TypeScript

The project uses TypeScript for type safety. Type definitions are in:

- `src/lib/api/types.ts` - API types
- `src/app.d.ts` - Global types

### Component Development

Svelte components use scoped CSS by default:

```svelte
<script lang="ts">
	// Component logic
</script>

<div class="component">
	<!-- HTML -->
</div>

<style>
	/* Scoped styles */
	.component {
		color: blue;
	}
</style>
```

### State Management

Use Svelte stores for shared state:

```typescript
import { writable } from 'svelte/store';

export const myStore = writable(initialValue);

// In component:
import { myStore } from './stores';
$myStore; // Access value
myStore.set(newValue); // Update
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - see LICENSE file for details
