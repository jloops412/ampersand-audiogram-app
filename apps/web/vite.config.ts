import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { copyFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const repositoryRoot = fileURLToPath(new URL('../../', import.meta.url));

function shipOpenSourceNotices() {
  return {
    name: 'ship-open-source-notices',
    closeBundle() {
      const legalDirectory = join(repositoryRoot, 'dist', 'legal');
      mkdirSync(legalDirectory, { recursive: true });
      copyFileSync(
        join(repositoryRoot, 'THIRD_PARTY_NOTICES.md'),
        join(legalDirectory, 'THIRD_PARTY_NOTICES.md'),
      );
      copyFileSync(
        join(repositoryRoot, 'infra', 'licenses', 'wavesurfer.js-7.12.11-LICENSE.txt'),
        join(legalDirectory, 'wavesurfer.js-7.12.11-LICENSE.txt'),
      );
    },
  };
}

export default defineConfig({
  root: 'apps/web',
  plugins: [react(), shipOpenSourceNotices()],
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/health': 'http://localhost:8080',
      '/healthz': 'http://localhost:8080',
    },
  },
  build: {
    outDir: '../../dist',
    emptyOutDir: true,
  },
});
