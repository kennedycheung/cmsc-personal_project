/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // jsdom's environment setup is expensive enough (~15s per worker with
    // this dependency tree) that spinning up several in parallel for a
    // 3-file suite risks blowing past the pool's worker-start timeout on
    // resource-constrained runners (observed flaking in both a local
    // Docker container and CI). Not worth the parallelism for a suite
    // this small.
    fileParallelism: false,
  },
});
