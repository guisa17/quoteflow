# QuoteFlow — Frontend

Consola de operador para RF-09: crear una solicitud, verla en la bandeja con
su `outcome`, abrir el detalle con trazabilidad completa, decidir
(aprobar/rechazar/observar) y ver el borrador final. Contrato fijo en
[`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md); vocabulario y reglas en
[`../REQUIREMENTS.md`](../REQUIREMENTS.md).

## Ejecutar

```bash
pnpm install
pnpm dev         # http://localhost:5173
```

No requiere que `backend/` esté corriendo. Por defecto arranca en **modo
mock**: un motor de reglas de negocio corre en el navegador (`src/mocks/`) y
la bandeja aparece poblada con los 8 escenarios de
[`backend/app/data/sample_requests.json`](../backend/app/data/sample_requests.json).
Es el mismo principio que `LLM_MODE=fake` en el backend — un camino
demostrable sin la dependencia externa.

```bash
cp .env.example .env   # opcional; el default ya es modo mock
pnpm build              # tsc -b && vite build
pnpm typecheck           # tsc -b --noEmit, sin emitir
pnpm test                # vitest run -- los 8 escenarios (AC-01..AC-08)
pnpm preview             # sirve dist/ ya construido
```

### Cambiar a la API real

`app/api/` todavía no existe en este repositorio (se construye en paralelo).
Cuando exista:

```bash
# .env
VITE_API_MODE=http
VITE_API_BASE_URL=http://localhost:8000
```

Ningún componente de `src/features/*` cambia — `src/api/requests.ts` es la
única capa que sabe si habla con `src/mocks/store.ts` o con
`src/api/client.ts` (axios contra `docs/API_CONTRACT.md`). El cliente HTTP
real ya está escrito y tipado contra el contrato; solo falta que el otro
lado exista para probarlo en serio.

## Qué se construyó

| Ruta | Cubre | Archivo principal |
|------|-------|--------------------|
| `/` | RF-09.2 — bandeja con `outcome`, motivo, búsqueda y filtro | `src/features/inbox/InboxPage.tsx` |
| `/new` | RF-09.1 — crear solicitud (`customer_id` + texto libre) | `src/features/new-request/NewRequestPage.tsx` |
| `/requests/:id` | RF-09.3/4/5 — extracción, cotización, riesgos, trazabilidad, panel de decisión, borrador | `src/features/request-detail/RequestDetailPage.tsx` |

El detalle compone las cinco secciones de RF-09.3-5 en una sola página
(cards apiladas): extracción → cotización → riesgos/motivos → panel de
decisión (solo si `outcome = PENDING_APPROVAL`) → borrador (solo si
`DRAFT_READY`) → trazabilidad. No hay tabs ni rutas separadas para esto: es
una sola vista de un caso, se lee de arriba hacia abajo en el mismo orden en
que el grafo lo procesó.

## El motor mock, no es una maqueta

`src/mocks/engine.ts` es un puerto línea por línea de
`backend/app/graph/nodes.py` + `app/domain/{validation,pricing,policy}.py`:
mismo orden de nodos, mismos códigos de motivo, mismo redondeo
`ROUND_HALF_UP` a centavo (`src/mocks/decimal.ts`, sin `float`).
`src/mocks/extract.ts` es el puerto de `app/llm/fake_extractor.py` (mismas
reglas de texto: SKU `XX-000`, cantidad más cercana, `N%`, sede).

Se verificó corriendo los 8 escenarios de `sample_requests.json` contra el
motor y comparando `outcome`/`reason_code`/cifras con
[`REQUIREMENTS.md` §5](../REQUIREMENTS.md) (AC-01…AC-08) — los 8 coinciden,
incluidas las cifras exactas de AC-01 (900.00 → 828.00 neto → 977.04 total)
y AC-03 (neto 12 900.00). Una solicitud nueva escrita en `/new` corre por
las mismas reglas, no por datos inventados — con la salvedad de que la
"extracción" es el mismo heurístico de texto del backend en modo fake, no un
LLM real: reconoce referencias con forma `XX-000` (de ahí el hint en el
formulario).

La idempotencia de `decision_id` (BR-15) y la pausa de `OBSERVE` (BR-14,
"el caso sigue en pausa") están implementadas en `src/mocks/store.ts`. Los
datos persisten en `localStorage` para sobrevivir a un refresh; el botón
"Reiniciar datos de demo" en la bandeja los regenera desde cero.

## Decisiones de diseño

- **Talonario y sello**: cada solicitud es un folio numerado y cada decisión
  humana, un sello con fecha y nombre. Los estados son tintes de copia
  autocopiativa (canario, celeste, verde, rosa, rojo), siempre con ícono y
  texto. Sistema completo en [`../DESIGN.md`](../DESIGN.md).
- **Archivo Variable + JetBrains Mono**: Archivo usa su eje de ancho para
  títulos y rótulos condensados; la mono tabular alinea montos, SKU y folios
  dígito a dígito.
- **Tema claro y oscuro**: sigue la preferencia del sistema, y el botón de la
  barra permite fijar uno (`src/lib/theme.ts`).
- **Recorrido de doce etapas** (`StageStrip`): cada nodo del grafo ocupa
  siempre la misma casilla, así dos solicitudes se comparan de un vistazo.
- **Atajos**: en el detalle, `J` y `K` recorren las solicitudes pendientes.
- **Radix solo donde aporta**: el selector de cliente usa
  `@radix-ui/react-select` (`src/components/ui/select.tsx`); el resto son
  elementos nativos con estilos propios.
- **TanStack Query** para el estado remoto (`src/hooks/useRequests.ts`):
  cache por id, invalidación tras crear/decidir, sin estado global propio —
  no hace falta más para tres pantallas.
- **Sin autenticación real**: el campo "Actor" del panel de decisión es
  texto libre (persistido en `localStorage` por comodidad de sesión, no por
  seguridad) — RF-09 no pide login, y agregarlo sería alcance no pedido
  (`PROJECT.md` §2.3).

## Verificación realizada

Esta sección fue verificada de forma independiente (sesión separada de la
que construyó el frontend), no solo tomada del reporte de esa sesión.

- `pnpm typecheck` limpio (`strict`, `noUnusedLocals`, sin `any` implícitos).
- `pnpm build` produce `dist/` sin errores (Vite 7, ~570 KB de bundle
  principal, sin code-splitting — aceptable para una consola de 3 pantallas).
- **`pnpm test` (Vitest, `src/mocks/engine.test.ts`): 11/11 en verde** — los
  8 escenarios de `sample_requests.json` corridos contra `src/mocks/engine.ts`
  de extremo a extremo, comparando `outcome`/`reason_code`/cifras exactas
  contra `REQUIREMENTS.md` §5 (AC-01…AC-08), más reanudación tras `APPROVE`
  y `REJECT` (AC-11). Reemplaza el script ad-hoc original: ahora es
  evidencia reproducible, no una afirmación de reporte.
- Instalación migrada de `npm` a `pnpm` (`pnpm-lock.yaml`), consistente con
  el resto de proyectos del autor.
- `pnpm audit`: 1 advisory alto en `react-router`
  ([GHSA-qwww-vcr4-c8h2](https://github.com/advisories/GHSA-qwww-vcr4-c8h2),
  CSRF en modo RSC). Verificado que no aplica: se confirmó por grep sobre
  `src/` que el proyecto usa `createBrowserRouter`/`RouterProvider` (modo
  *data router* del lado del cliente) — ningún import de
  `react-router/rsc` ni de Server Components. Se documenta como riesgo
  evaluado y descartado en vez de forzar el salto a v8 (breaking) sin
  tiempo de regresión.

## Pendiente / fuera de alcance

- `app/api/` real no existe todavía — el cliente HTTP (`src/api/client.ts`)
  está escrito y tipado contra el contrato pero no se pudo probar contra un
  servidor real. Cuando exista, `VITE_API_MODE=http` es el único cambio
  necesario.
- Sin i18n, dark mode toggle ni autenticación — fuera de alcance
  (`PROJECT.md` §2.3).
