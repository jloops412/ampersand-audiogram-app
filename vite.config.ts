import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // The output directory will be 'dist', which our backend server expects
    outDir: 'dist'
  }
})
