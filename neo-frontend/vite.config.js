import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue' // <--- Fíjate en el '@vitejs/'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  base: '/', 
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    chunkSizeWarningLimit: 1000,
  }
})