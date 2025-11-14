# Using Full Bun Stack (Experimental)

⚠️ **Warning**: This is experimental and not officially supported by SvelteKit.

## Setup

If you want to try Bun's bundler instead of Vite:

### 1. Create a custom build script

```typescript
// frontend/build.ts
import { build } from 'bun';

// Production build
await build({
  entrypoints: ['./src/index.ts'],
  outdir: './dist',
  target: 'browser',
  minify: true,
  sourcemap: 'external',
});
```

### 2. Update package.json

```json
{
  "scripts": {
    "dev": "bun --hot src/main.ts",
    "build": "bun run build.ts",
    "preview": "bun run --cwd dist index.js"
  }
}
```

### 3. Challenges

- SvelteKit expects Vite's plugin system
- You'd need to manually handle Svelte compilation
- HMR would be more basic
- Loss of SvelteKit's routing and features

## Verdict

**Not recommended** for SvelteKit projects. The current Bun + Vite setup gives you:
- All of Bun's speed benefits
- All of Vite's stability and features
- Official SvelteKit support

## Future

Bun is working on better framework integration. Watch:
- https://github.com/oven-sh/bun/issues (SvelteKit support)
- SvelteKit adapter-bun (community project)

When official support arrives, switching will be easy!
