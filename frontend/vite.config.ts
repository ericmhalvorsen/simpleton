import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 5173,
		host: '0.0.0.0',
		hmr: {
			overlay: true
		},
		// Configure proxy for API requests
		proxy: {
			'^/api': {
				target: 'http://simpleton:8000',
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	},
	resolve: {
		alias: {
			$lib: resolve(__dirname, './src/lib'),
			$app: resolve(__dirname, './.svelte-kit/runtime/app')
		}
	},
	// Add type checking during build
	build: {
		target: 'esnext',
		minify: 'esbuild',
		sourcemap: true
	},
	// Handle environment variables
	define: {
		'import.meta.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || '/api'),
		'import.meta.env.VITE_API_KEY': JSON.stringify(process.env.VITE_API_KEY || '')
	}
});
