import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base relativa: o site roda em GitHub Pages sob /<repo>/ sem reconfigurar
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { chunkSizeWarningLimit: 1500 },
})
