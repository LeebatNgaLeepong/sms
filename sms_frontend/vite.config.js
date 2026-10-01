import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // React and friends are CommonJS. Left to discovery, the dep optimizer
  // pre-bundles react.js exporting only a named `t` binding and no default,
  // while the app's transform reads the default and indexes it for useState.
  // That leaves useState undefined and the first hook call throws, showing as a
  // blank page or an undefined hook. Listing them explicitly makes the
  // optimizer emit the interop wrapper the transform expects.
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-dom/client',
      'react/jsx-dev-runtime',
      'react-router-dom',
    ],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
