import { defineConfig } from 'vite'
import vue from '@vue/plugin-vue' // Asegúrate de que el nombre sea correcto según tu package.json
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  // En Vercel la base debe ser la raíz para evitar errores 404 en los assets
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
      // Este proxy SOLO funciona en local (npm run dev)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  },

  build: {
    // Aumentamos el límite para que no te salgan advertencias por el tamaño de ApexCharts
    chunkSizeWarningLimit: 1000,
  }
})