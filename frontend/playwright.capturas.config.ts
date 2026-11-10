import { defineConfig } from '@playwright/test'

/**
 * Genera las capturas del README (`docs/img/`) desde la app real en modo demo.
 * No es una prueba ni corre en el CI: se ejecuta a mano cuando cambia la interfaz.
 *
 *   pnpm capturas
 */
const PORT = 4181

export default defineConfig({
  testDir: './e2e',
  testMatch: 'capturas.shots.ts',
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${PORT}`,
    locale: 'es-PE',
    timezoneId: 'America/Lima',
    browserName: 'chromium',
  },
  webServer: {
    command: `pnpm exec vite --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}`,
    env: { VITE_API_MODE: 'mock' },
    reuseExistingServer: false,
    timeout: 60_000,
  },
})
