/**
 * Selector de fuente de datos (ver `.env.example`).
 *
 * `mock`  -> `src/mocks/*` corre el mismo motor de reglas en el navegador,
 *            sin red. Es el valor por defecto, para mostrar la UI sin backend.
 * `http`  -> `src/api/client.ts` llama a la API real (`docs/API_CONTRACT.md`).
 */
export const API_MODE: 'mock' | 'http' = import.meta.env.VITE_API_MODE === 'http' ? 'http' : 'mock'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
