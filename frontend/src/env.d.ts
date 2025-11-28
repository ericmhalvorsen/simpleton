/// <reference types="@sveltejs/kit" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_API_KEY: string;
  // Add other environment variables here as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
