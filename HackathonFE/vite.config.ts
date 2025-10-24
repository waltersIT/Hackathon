import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,              // Force port 5173, PREVENTS FUTURE ISSUES FOR OTHERS HOPEFULLY
    strictPort: true,        // Exits if 5173 is already being used instead of jumping to next available port and running into CORS errors
  },
})