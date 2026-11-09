# IMPACT — Mapa de módulos y propagación de cambios

Responde a tres preguntas: qué participa en el flujo, qué se mueve al cambiar una política, y qué evidencia de este mapa condicionó el plan de trabajo.

> **Origen del mapa.** Este documento es la lectura de negocio, curada a mano: qué participa en el flujo y qué se propaga al cambiar una política. El reporte generado por la herramienta en sí —extracción automática por AST, comunidades, nodos más conectados, ciclos de import— vive en [`docs/graphify/GRAPH_REPORT.md`](docs/graphify/GRAPH_REPORT.md) y está regenerado sobre el código final (incluye `app/api/`). Ambos se complementan, no se duplican: uno es análisis estructural, el otro es interpretación de negocio; la §3 de este documento los cruza.

---

## 1. Módulos que participan en el flujo

```
   frontend/  ──HTTP──►  ┌──────────────────────────────┐
   (React, tipos                │   app/api                │  expone y serializa
    generados del contrato)     │   schemas · routes       │  · sin reglas
                                │   mapping  · store       │
                                └──────┬─────────────┬─────┘
                                       │             │
                                       │             └──► tabla `requests`
                                       │                  (cache de bandeja)
                                ┌──────▼───────┐
                                │  app/graph   │  orquesta · enruta · interrumpe
                                │  state · nodes · routing · build · checkpointer
                                └───┬──────┬───┘
                                    │      │
                      ┌─────────────┘      └──────────────┐
                      │                                   │
               ┌──────▼───────┐                    ┌──────▼───────┐
               │  app/domain  │                    │   app/llm    │
               │  DETERMINISTA│                    │  NO DETERM.  │
               │  models · repositories            │  extractor fake
               │  pricing · policy · validation    │  (real: LOOP.md,
               │  tools                            │   no ejecutado)
               └──────┬───────┘                    └──────────────┘
                      │                                   ▲
               ┌──────▼───────┐                           │
               │ app/data/*.json                    texto del cliente
               │ customers · products                (entrada no confiable)
               │ inventory · policies
               └──────────────┘
```

**Las dos relaciones que sostienen la arquitectura**, ambas verificables de un vistazo:

1. **`app/domain` no importa nada de `app/llm`.** La flecha nunca va en esa dirección — es lo que hace cumplir [ADR-002](docs/adr/ADR-002-frontera-determinista.md) y lo primero que hay que comprobar ante cualquier duda sobre si un cambio respeta la frontera.
2. **`app/api` no importa nada de `app/domain` salvo tipos y enums.** Traduce y serializa (`mapping.py`); toda decisión sigue viniendo del grafo. Si algún día `routes.py` empieza a comparar un monto contra un umbral, esa regla se escapó de `app/domain/policy.py`.

**Sobre la tabla `requests`:** es un cache denormalizado para la bandeja (RF-02), no una segunda fuente de verdad. El estado real de cada ejecución vive en el checkpointer; esta tabla solo evita reconstruirlo N veces por cada listado. Si divergen, el checkpointer gana — la tabla se puede reconstruir, el checkpoint no.

### Participación por resultado

Qué módulos intervienen según dónde termina la solicitud:

| Resultado | `llm` | `domain` | `graph` | Humano |
|-----------|:-----:|:--------:|:-------:|:------:|
| `NEEDS_CLARIFICATION` | ✓ | validation | routing | — |
| `BLOCKED` | ✓ | repositories · validation | routing | — |
| `REJECTED_BY_POLICY` | ✓ | policy | routing | — |
| `PENDING_APPROVAL` | ✓ | pricing · policy | routing · checkpointer | ✓ |
| `DRAFT_READY` | ✓ (extrae y redacta) | todo | todo | opcional |

Los tres primeros resultados **no requieren cálculo de precios**: se resuelven antes. Esto explica el orden de los nodos en [PROJECT.md](PROJECT.md) §4.2 — validar y consultar inventario antes de cotizar evita calcular sobre datos que van a bloquearse.

## 2. Qué cambia al modificar una política

Escenario concreto: **bajar el descuento máximo de `GOLD` de 12 % a 7 %**.

### Lo que se toca

| Paso | Archivo | Cambio |
|------|---------|--------|
| 1 | `app/data/policies.json` | `discount_by_tier.GOLD.max_discount_pct: 12.0 → 7.0` |

**Eso es todo el cambio de código.** Un solo valor, en un archivo de datos.

### Lo que se propaga automáticamente

| Módulo | Efecto |
|--------|--------|
| `domain/repositories.py` → `PolicyRepository` | Lee el nuevo valor; sin cambios |
| `domain/policy.py` | Recalcula la excepción con el nuevo máximo; sin cambios |
| `graph/nodes.py` → `evaluate_policy` | Emite `DISCOUNT_EXCEPTION` donde antes no lo hacía; sin cambios |
| `graph/routing.py` | Enruta a `human_approval` en más casos; sin cambios |
| API y frontend | Muestran el nuevo motivo; sin cambios |

### Lo que cambia de comportamiento

El escenario `S1` —el caso de referencia— **cambia de resultado**:

| | Antes (GOLD 12 %) | Después (GOLD 7 %) |
|---|---|---|
| Descuento solicitado | 8 % | 8 % |
| ¿Dentro de política? | Sí (8 ≤ 12) | **No** (8 > 7) |
| Resultado | `DRAFT_READY` | **`PENDING_APPROVAL` / `DISCOUNT_EXCEPTION`** |

### Lo que hay que actualizar a mano

| Artefacto | Por qué |
|-----------|---------|
| `backend/app/data/sample_requests.json` | El `expected_outcome` de `S1` deja de ser cierto |
| `REQUIREMENTS.md` §5, AC-01 | El criterio de aceptación referencia el resultado anterior |
| `tests/integration/test_scenarios.py` | Falla, correctamente: la política cambió |

**Que el test falle es el comportamiento deseado.** Un cambio de política que no rompe ninguna prueba indicaría que las pruebas no están verificando la política.

### Lo que nunca cambia

Prompts, estructura del grafo, contrato de la API, esquema de la base de datos. Una política es un dato, no código — es el resultado directo de [ADR-002](docs/adr/ADR-002-frontera-determinista.md), y es lo que permite responder en vivo a una modificación durante la presentación.

## 3. Qué evidencia del mapa influyó en el plan

Cuatro observaciones del mapa se tradujeron en decisiones concretas de [PHASE_01.md](PHASE_01.md):

| Observación en el mapa | Efecto en el plan |
|------------------------|-------------------|
| `domain` no depende de `graph` ni de `llm`: es una hoja del grafo de dependencias | El dominio se construye y se prueba **primero y completo** (T2-T6), antes de tocar LangGraph. Sus pruebas no necesitan Postgres ni modelo, así que corren en cualquier entorno |
| `graph/state.py` es el punto por el que pasan todos los nodos | Es tarea propia (T7) y uno de los dos únicos archivos con `mypy` obligatorio. Un error de tipo ahí se propaga a los 12 nodos |
| `llm` tiene una sola entrada (`Protocol` de extractor) y ninguna salida hacia el dominio | Permite sustituirlo por un extractor determinista (T8) y satisfacer la suite offline (RF-10) sin duplicar lógica |
| El `checkpointer` es la única dependencia de infraestructura del flujo | Se aísla en T11, después de que el grafo ya funcione en memoria. Así un fallo de Postgres no bloquea el avance del resto |

Y una quinta observación condicionó el diseño de datos: **`policies.json` es leído por un solo módulo** (`PolicyRepository`). Esa concentración es lo que hace posible la sección 2 de este documento. Si la política se leyera desde varios puntos, cambiarla dejaría de ser un cambio de un valor y pasaría a ser una refactorización.

**Contraste contra el código real (proyecto completo):** el reporte de [`docs/graphify/GRAPH_REPORT.md`](docs/graphify/GRAPH_REPORT.md), regenerado sobre el código final (265 nodos, 588 aristas, 15 comunidades), confirma las cinco observaciones sin ajustes:

- **`QuoteState` es el nodo más conectado** (38 aristas), seguido de los enumerados del dominio (`ReasonCode` 31, `DecisionAction` 26, `AuditEvent` 23). Coincide con la observación 2: es el punto por el que pasan todos los nodos, y por eso tiene `mypy` obligatorio.
- **Las comunidades detectadas separan limpiamente las capas**: dominio (`PolicyEvaluation`, `calculate_quote`, `tools.py`), grafo (`build_graph`), LLM (`FakeExtractor`, `prompts.py`) y API (`decide_request`) aparecen como grupos distintos, sin mezclarse.
- **Sin ciclos de import** — la frontera de ADR-002 se sostiene estructuralmente, no solo por convención.

El mapa de esta sección deja de ser "de diseño" y pasa a estar verificado contra el código construido.

---

**Relacionados:** [PROJECT.md](PROJECT.md) · [PHASE_01.md](PHASE_01.md) · [ADR-002](docs/adr/ADR-002-frontera-determinista.md) · [REQUIREMENTS.md](REQUIREMENTS.md)
