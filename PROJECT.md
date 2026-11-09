# PROJECT — QuoteFlow

Fuente de verdad del proyecto. Si el código y este documento discrepan, uno de los dos está mal: se corrige en el mismo ciclo.

- **Autor:** Guillermo Salcedo.
- **Alcance:** MVP de una vertical completa. Las decisiones de priorización de §2.1 responden a esa acotación, no a limitaciones técnicas.

---

## 1. Objetivo

Construir una vertical funcional que convierta una **solicitud de cotización en texto libre** en **uno de cinco resultados auditables**, mediante un workflow LangGraph con estado tipado, cálculo determinista y pausa real para decisión humana, persistido de forma durable.

El criterio de éxito no es la cantidad de funcionalidades: es que el sistema **haga exactamente lo que promete y lo demuestre con evidencia reproducible**.

## 2. Alcance

### 2.1 Resultados priorizados

Tres casos concentran el valor del producto: uno estándar, uno incompleto y uno con aprobación. Esos tres reciben la profundidad:

| Prioridad | Resultado | Justificación |
|-----------|-----------|---------------|
| **P0** | `DRAFT_READY` | Camino feliz completo: extracción → dominio → cálculo → borrador |
| **P0** | `NEEDS_CLARIFICATION` | Demuestra que el sistema **no cotiza** con información insuficiente |
| **P0** | `PENDING_APPROVAL` | Demuestra `interrupt()`, reanudación durable e idempotencia — el núcleo técnico del proyecto |
| P1 | `BLOCKED` | Se resuelve con la misma consulta determinista al catálogo y al inventario; costo marginal cercano a cero |
| P1 | `REJECTED_BY_POLICY` | Cierra la defensa contra inyección de prompt; costo marginal ~0 |

Los cinco resultados se implementan. La diferencia P0/P1 está en la cobertura de pruebas y en el detalle del borrador, no en si existen.

### 2.2 Alcance funcional

1. Registrar una solicitud (`customer_id` + texto libre).
2. Extraer con salida estructurada: ítems, cantidades, sede, fecha requerida, descuento solicitado.
3. Consultar dominio local: clientes, catálogo, inventario, precios, política.
4. Enrutar: completo / aclaración / SKU desconocido / sin stock / sujeto a aprobación / rechazo.
5. Calcular precio, descuento permitido y totales **solo** con funciones deterministas.
6. Pausar con `interrupt()`, sobrevivir a reinicio del proceso, reanudar con la decisión humana.
7. Emitir borrador y registro de auditoría legible (estados, nodos, decisiones, errores).
8. UI de operador: crear solicitud, bandeja, detalle con trazabilidad, aprobar/rechazar/observar, ver borrador.

### 2.3 No alcance

Declarado en [BUSINESS_CASE.md §4](BUSINESS_CASE.md). Resumen: envío automático al cliente, autenticación empresarial, integraciones reales (email/WhatsApp/ERP), facturación, reserva efectiva de stock, escalas de precio por volumen, negociación multironda, infraestructura productiva, diseño visual avanzado.

**Deuda aceptada conscientemente** (se registra en `EVIDENCE.md`, no se oculta):
- Un solo idioma en el borrador (español).
- Sin paginación en la bandeja: el volumen del MVP no la justifica.
- Sin reintentos con backoff ante fallo del LLM: un fallo de extracción degrada a `NEEDS_CLARIFICATION` con el error registrado, que es el comportamiento seguro.

## 3. Stack y justificación

| Capa | Elección | Por qué esta y no otra |
|------|----------|------------------------|
| Lenguaje/API | Python 3.12 + FastAPI | LangGraph es Python-first: los checkpointers de Postgres y `interrupt()` tienen ahí la implementación de referencia. FastAPI + Pydantic dan el **estado tipado** sin machinery adicional |
| Paquetes | `uv` | Lockfile reproducible e instalación en frío rápida — el DoD pide ejecutar desde un entorno limpio |
| Orquestación | **LangGraph** `StateGraph` | Estado explícito, rutas condicionales, `interrupt()` |
| Persistencia | PostgreSQL + `AsyncPostgresSaver` | La memoria en proceso no sobrevive a un reinicio. Permite demostrar reanudación tras reinicio |
| Frontend | React + Vite + TypeScript | Consola de operador, sin SSR ni SEO. Vite evita configuración de build y mantiene corto el ciclo de feedback |
| Calidad | `ruff` + `mypy` (no strict) | Tipado donde protege: estado del grafo y dominio. El modo estricto no se justifica en el alcance del MVP |
| Pruebas | `pytest` + extractor fake | Requisito: **modo test sin depender de un modelo externo** |
| Infra local | Docker Compose (Postgres) | Solo para levantar la base. Sin optimizaciones de producción |

## 4. Arquitectura

### 4.1 Frontera de responsabilidad (decisión central — [ADR-002](docs/adr/ADR-002-frontera-determinista.md))

```
  Texto libre del cliente  ──►  [ LLM ]  ──►  Extracción estructurada validada
                                                        │
                                                        ▼
                                          [ DOMINIO DETERMINISTA ]
                                    clientes · catálogo · inventario
                                       precios · política comercial
                                                        │
                                                        ▼
                                     Decisión de routing + cotización
                                                        │
                                                        ▼
                                          [ HUMANO ] aprueba / rechaza
                                                        │
                                                        ▼
                                    [ LLM ] redacta borrador  (opcional)
```

El LLM ocupa **solo los extremos**: interpretar entrada y redactar salida. Nunca decide precio, stock, descuento, aprobación ni routing. Si el LLM no está disponible, el sistema sigue siendo correcto (extracción degradada → aclaración; redacción → plantilla determinista).

### 4.2 Nodos del grafo

| Nodo | Responsabilidad | Determinista |
|------|-----------------|--------------|
| `ingest` | Normaliza la solicitud, abre `thread_id`, registra evento inicial | Sí |
| `extract` | Salida estructurada del LLM → `Extraction` validada con Pydantic | No (LLM) |
| `resolve_customer` | Busca cliente; si no existe → tier conservador + flag `UNKNOWN_CUSTOMER` | Sí |
| `resolve_catalog` | Mapea a SKU **por coincidencia exacta**; sin sustitución inventada | Sí |
| `validate_request` | Completitud e integridad → `NEEDS_CLARIFICATION` / `BLOCKED` | Sí |
| `check_inventory` | Disponible = `on_hand − reserved` | Sí |
| `price_quote` | Subtotal, descuento permitido, neto, IGV, total | Sí |
| `evaluate_policy` | Umbral, excepción de descuento, techo duro, cliente desconocido | Sí |
| `human_approval` | `interrupt()` — pausa durable | Sí |
| `apply_decision` | Aplica decisión con idempotencia por `decision_id` | Sí |
| `compose_draft` | Redacta el borrador (LLM o plantilla en modo test) | No (LLM) |
| `finalize` | Fija `outcome`, cierra auditoría | Sí |

Rutas condicionales tras `validate_request`, `check_inventory`, `evaluate_policy` y `apply_decision`.

### 4.2.1 Herramientas locales de dominio

El flujo consulta cinco herramientas locales: clientes, catálogo, inventario, precios y política comercial.

Esas cinco herramientas existen en `app/domain/tools.py` y **las invocan los nodos del grafo, no el modelo**. La distinción es deliberada: exponerlas al LLM como herramientas enlazadas le daría acceso a inventario y política, lo que contradice [ADR-002](docs/adr/ADR-002-frontera-determinista.md). Así el flujo usa herramientas sin ceder la decisión.

| Herramienta | Devuelve | Usada por |
|-------------|----------|-----------|
| `lookup_customer(customer_id)` | Cliente y nivel, o ausencia explícita | `resolve_customer` |
| `lookup_product(sku)` | Producto activo del catálogo, o `None` | `resolve_catalog` |
| `check_availability(sku, qty)` | `on_hand − reserved` y si cubre la cantidad | `check_inventory` |
| `get_unit_price(sku)` | Precio de lista en `Decimal` | `price_quote` |
| `get_policy()` | Máximos por nivel, techo duro, umbral, IGV | `evaluate_policy` |

### 4.2.2 Fallo recuperable

Es un caso de routing propio, distinto de los demás. Se materializa así: si la extracción falla o no valida contra el esquema, se reintenta **una vez**; si vuelve a fallar, la solicitud termina en `NEEDS_CLARIFICATION` con `EXTRACTION_FAILED` y el error queda en la auditoría (RF-05).

El sistema nunca cotiza sobre una extracción no validada: ante la duda, pregunta.

### 4.3 Estructura del repositorio

```
quoteflow/
├── README.md                    # ejecutar app + tests desde entorno limpio
├── AGENTS.md                    # instrucciones persistentes para asistentes
├── BUSINESS_CASE.md  PROJECT.md  REQUIREMENTS.md
├── ROADMAP.md  PHASE_01.md  STATE.md  EVIDENCE.md  IMPACT.md
├── AI_USE.md  LOOP.md
├── docs/adr/                    # ADR-001 …
├── docker-compose.yml           # solo Postgres
├── backend/
│   ├── pyproject.toml  .env.example
│   ├── app/
│   │   ├── main.py              # FastAPI
│   │   ├── api/                 # rutas HTTP
│   │   ├── domain/              # funciones deterministas + repositorios + herramientas locales
│   │   ├── graph/               # state.py · nodes.py · build.py
│   │   ├── llm/                 # extractor real + extractor fake (tests)
│   │   └── data/*.json          # seed ficticio versionado
│   └── tests/                   # unitarias + integración
└── frontend/                    # React + Vite
```

## 5. Restricciones

- Sin credenciales en el repositorio; `.env.example` obligatorio.
- El seed de dominio se versiona en Git: la evidencia debe ser reproducible byte a byte.
- El texto del cliente **nunca** se interpola en el prompt como instrucción; siempre como dato delimitado.
- Un test que dependa de red o de un LLM externo no cuenta como test verde.

## 6. Criterios de aceptación (nivel proyecto)

El detalle verificable está en [REQUIREMENTS.md §4](REQUIREMENTS.md). A nivel proyecto, una versión está lista cuando:

| # | Criterio |
|---|----------|
| A1 | La app se levanta y el flujo principal se recorre siguiendo solo el README, desde entorno limpio |
| A2 | Se demuestran los casos estándar (`S1`), incompleto (`S2`) y con aprobación (`S3`/`S4`) |
| A3 | Una ejecución interrumpida en `human_approval` se reanuda **después de reiniciar el backend** |
| A4 | Ninguna cotización usa un precio, stock, cliente o descuento ausente del seed |
| A5 | `pytest` pasa completo sin acceso a un LLM externo |
| A6 | Reenviar la misma decisión humana no produce efecto duplicado |
| A7 | `STATE.md`, `EVIDENCE.md` y los ADR coinciden con el código en cada versión |

---

**Relacionados:** [BUSINESS_CASE.md](BUSINESS_CASE.md) · [REQUIREMENTS.md](REQUIREMENTS.md) · [STATE.md](STATE.md) · [AI_USE.md](AI_USE.md)
