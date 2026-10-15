import { readFileSync } from 'node:fs';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const { version } = JSON.parse(readFileSync(new URL('./package.json', import.meta.url)));

export default defineConfig({
  plugins: [react()],
  // Shown in the footer: bumping package.json "version" is the visible change in the live demo.
  define: { __APP_VERSION__: JSON.stringify(version) },
  // `npm run dev` proxies the API like nginx and the Ingress do, so the code always calls /api.
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
});
