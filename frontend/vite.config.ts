import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const DEPLOYED_API = 'https://a814vaktx0.execute-api.ap-south-1.amazonaws.com/prod'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/cities': {
        target: DEPLOYED_API,
        changeOrigin: true,
      },
      '/clusters': {
        target: DEPLOYED_API,
        changeOrigin: true,
      },
      '/impact': {
        target: DEPLOYED_API,
        changeOrigin: true,
      },
      '/subscribe': {
        target: DEPLOYED_API,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'node',
  },
})
