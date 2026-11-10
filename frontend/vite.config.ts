import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, searchForWorkspaceRoot } from 'vite'

// Seed de dominio compartido con el backend (ADR-001): una sola fuente.
const seedDir = path.resolve(__dirname, '../backend/app/data')

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@seed': seedDir,
    },
  },
  server: {
    port: 5173,
    // El servidor de desarrollo solo sirve archivos dentro del proyecto;
    // el seed vive fuera de frontend/, asi que se permite explicitamente.
    fs: {
      allow: [searchForWorkspaceRoot(process.cwd()), seedDir],
    },
  },
})
