import { defineConfig, devices } from '@playwright/test'

/**
 * Pruebas end-to-end en un navegador real (L-09). Corren contra la consola en
 * modo demo: el motor de reglas corre en el navegador sobre el mismo seed que
 * el backend, así que no hace falta Postgres ni LLM.
 *
 *   pnpm test:e2e          # levanta vite en :4180 y corre las pruebas
 *   pnpm test:e2e --ui     # modo interactivo
 *
 * Los archivos son `*.e2e.ts`, para que Vitest no los tome como suyos.
 */
const PORT = 4180

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.e2e.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: `http://localhost:${PORT}`,
    locale: 'es-PE',
    timezoneId: 'America/Lima',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'escritorio', use: { ...devices['Desktop Chrome'] } },
    { name: 'movil', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: `pnpm exec vite --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}`,
    env: { VITE_API_MODE: 'mock' },
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
