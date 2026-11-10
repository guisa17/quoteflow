# AI_USE — Uso de asistentes de IA en el desarrollo de QuoteFlow

Registro de qué herramientas se usaron, con qué rol, qué outputs se aceptaron o rechazaron y cómo se verificó cada resultado.
**No contiene razonamiento interno ni transcripciones.**

La especificación se usó como fuente de verdad durante todo el desarrollo: cada regla y cada criterio se contrastó antes de darse por completo (método en §3).

---

## 1. Herramientas y rol asignado

| Herramienta | Rol asignado | Qué **no** se le delegó |
|-------------|--------------|-------------------------|
| Claude Code (Opus), sesión principal | Especificación, arquitectura, dominio determinista (T2-T6), tareas de alto riesgo de corrección (T11-T14), revisión y verificación independiente del trabajo delegado | La definición de las reglas de negocio, la calibración del seed, la aceptación de cualquier resultado |
| Claude Code (Sonnet), sesiones delegadas | Implementación mecánica contra un contrato ya fijo y probado: el grafo LangGraph (T7-T10) contra el dominio ya cerrado; el frontend contra `docs/API_CONTRACT.md` ya fijo | La definición del contrato que consumen, la arquitectura del grafo, el veredicto final sobre si su resultado se acepta |

**Por qué esta división:** el dominio y las pruebas de correctitud (T11-T14) concentran el juicio de negocio y los errores más caros de no detectar; el grafo y el frontend son implementación disciplinada contra un contrato ya escrito. La sesión principal delega solo cuando existe ese contrato fijo, y siempre revisa el resultado antes de aceptarlo.

**Modelo de trabajo:** especificación en Markdown primero (`PROJECT.md`, `REQUIREMENTS.md`), código después. El asistente implementa contra reglas con identificador (`BR-xx`, `RF-xx`); no infiere reglas a partir del código.

**Responsabilidad:** la responsabilidad sobre el código, las decisiones y la verificación no se delega al asistente. Ningún output se incorporó sin la comprobación descrita en §3.

### Gobierno de la sesión de trabajo

La cantidad de agentes o comandos no es un objetivo. El proyecto se organizó contra estos criterios:

| Criterio | Cómo se cumple aquí |
|---|---|
| Un solo hilo de gobierno | Una sesión de trabajo, con [CLAUDE.md](../../CLAUDE.md) como única fuente de reglas cargada en cada turno |
| Tareas acotadas | Cada unidad de trabajo tiene identificador y Definition of Done propio: `T0-T14` en [PHASE_01.md](PHASE_01.md), el ciclo de [LOOP.md](LOOP.md) |
| Contexto persistente | [STATE.md](STATE.md) y [EVIDENCE.md](EVIDENCE.md) permiten retomar el trabajo sin reconstruir la conversación previa |
| Aislamiento cuando haya trabajo paralelo | El dominio (T2-T6) se construyó en un solo hilo, sin paralelismo: sus módulos comparten un mismo estado tipado ([IMPACT.md](../IMPACT.md) §1) y ejecutarlos a la vez habría producido colisiones sin ganancia. Una vez que el dominio y el contrato de API quedaron fijos y probados, se abrió trabajo paralelo real — una sesión para el grafo (`backend/`), otra para el frontend (`frontend/`) — con aislamiento por **disjunción de archivos**: ninguna de las dos sesiones delegadas tocó `STATE.md`, `EVIDENCE.md` ni `PHASE_01.md`. Se sostuvo en la práctica: ambas sesiones corrieron a la vez (backend T7-T11 y frontend simultáneamente), sin un solo conflicto de archivos ni de commit al consolidar |
| Verificación independiente | [LOOP.md](LOOP.md) separa worker de verifier para el ciclo de extracción. El mismo patrón se aplicó al grafo delegado: la sesión de Sonnet comiteó T7-T10, y la sesión principal corrió `pytest`/`ruff`/`mypy` de forma independiente antes de aceptar el resultado y continuar con T11 |

Intentar aislamiento por *worktree* de verdad (una copia de árbol de trabajo separada por sesión) falló en este entorno: la herramienta lo requiere en la raíz del directorio de trabajo primario, que no es la raíz del repositorio Git aquí. El aislamiento efectivo terminó siendo por convención (qué archivos toca cada sesión), no por mecanismo — una limitación de la herramienta, no de la decisión de diseño.

## 2. Outputs aceptados y rechazados

| # | Output propuesto | Decisión | Motivo |
|---|------------------|----------|--------|
| 1 | Calibración del seed para que el caso de referencia (20 × HX-200, GOLD, 8 %) termine en `DRAFT_READY` | **Aceptado** | Recalculado a mano: 900.00 → 72.00 → 828.00 < 10 000. Coherente con la política del seed |
| 2 | Priorizar 3 de los 5 resultados | **Ajustado** | El planteamiento inicial sugería implementar solo 2-3. Los casos estándar, incompleto y con aprobación son los principales, y los otros dos resultados se resuelven con la misma consulta determinista al catálogo y al inventario, con costo marginal cercano a cero. Se implementan los cinco, concentrando la profundidad de pruebas en esos tres |
| 3 | Escala de precio por volumen en el catálogo | **Rechazado** | Añade una segunda dimensión de descuento que interactúa con la política por nivel y vuelve el cálculo difícil de auditar a mano. Declarado como no alcance en `BUSINESS_CASE.md` §4 |
| 4 | Campos de dominio no usados en el seed (límite de crédito, cliente inactivo) | **Rechazado** | Datos que no alimentan ninguna regla son ruido: sugieren capacidades que el sistema no tiene |
| 5 | Instalar `gsd-core` como herramienta de orquestación del propio desarrollo | **Rechazado** | Genera su propia estructura de artefactos, que compite con los documentos del proyecto, y su ejecución en oleadas paralelas no encaja con el criterio de un solo hilo de gobierno. Detalle en §1 y en `docs/REFERENCES.md` |
| 6 | T7-T10 (grafo LangGraph) implementados por una sesión delegada de Sonnet, briefeada solo con los documentos del repositorio | **Aceptado tras verificación independiente** | La sesión principal corrió `pytest`/`ruff`/`mypy` sobre el resultado antes de continuar — 111 tests en verde, sin tocar `app/domain/`. El diseño (`_resolve_extractor` falla explícito si `LLM_MODE=real` sin el extractor real construido, en vez de degradar en silencio) se revisó y se consideró correcto |
| 7 | Reiniciar procesos de Docker Desktop directamente para resolver un cuelgue del motor durante T11 | **Rechazado** | Es una acción con efecto fuera del proyecto (podía interrumpir otro trabajo del usuario en Docker). Se prefirió `wsl --shutdown` primero (más acotado) y, cuando no bastó, pedir confirmación explícita antes de un reinicio completo del sistema |
| 8 | Copiar el sistema de diseño de `bento-app` tal cual para el frontend de QuoteFlow | **Ajustado a instrucción explícita** | El usuario corrigió: usarlo como referencia de principios (acento único, sin sombras, shadcn/ui), no como plantilla — QuoteFlow tiene un alcance visual deliberadamente más simple ("diseño visual avanzado" está fuera de alcance, `PROJECT.md` §2.3). El brief a la sesión delegada de frontend se ajustó antes de lanzarla |
| 9 | `REQUIREMENTS.md` AC-11 ("`REJECT` ⇒ `REJECTED`") vs. el código ya delegado (`finalize` reutiliza `REJECTED_BY_POLICY`, sin un `Outcome` separado) | **Se corrigió el documento, no el código** | El código y su test unitario ya tenían la interpretación correcta, consistente con que "rechazado o escalado por política" es un solo resultado. La especificación tenía la redacción imprecisa por escribirse antes de que existiera el enum. Ver `EVIDENCE.md` E-09 |
| 10 | Registrar explícitamente los tipos propios de `QuoteState` en el serializador msgpack del checkpointer (`allowed_msgpack_modules`) | **Aceptado** | LangGraph advertía que el modo permisivo por defecto (deserializa tipos no registrados con un warning) puede volverse estricto en una versión futura. Se prefirió depender de un registro explícito, verificable, a depender de un comportamiento por defecto que puede cambiar. Ver `EVIDENCE.md` E-09 |
| 11 | Frontend completo (RF-09) implementado por una sesión delegada de Sonnet | **Aceptado con correcciones tras verificación independiente** | Aislamiento confirmado (`git show --stat` filtrado: cero archivos fuera de `frontend/`). Tres afirmaciones del reporte propio de la sesión no se aceptaron sin comprobar: (a) el gestor de paquetes era `npm`, corregido a `pnpm` tras señalarlo el usuario; (b) la verificación de los 8 escenarios era "un script ad-hoc, no quedó como suite Vitest" — cita literal de su reporte — se agregó una suite real (`engine.test.ts`, 11/11); (c) el descarte de un advisory de seguridad de `react-router` se re-verificó por grep sobre el código en vez de aceptarse de palabra, y resultó correcto. Ver `EVIDENCE.md` E-10 |
| 12 | Dar por buena la aplicación porque los 139 tests pasaban | **Rechazado** | Se arrancó el servidor real (`uvicorn`) y se clonó el repositorio en limpio. Ambas comprobaciones encontraron bugs que la suite no detectaba: el `loop_factory` de `uvicorn` (E-11) y el `.env` que nunca se leía (E-12). Ninguno era detectable por tests, porque los tests no arrancan el servidor real ni dependen de valores de `.env` distintos al default. Es la razón por la que "pruebas en verde" y "aplicación ejecutable" son criterios **separados** |

## 3. Cómo se verificó cada resultado

| Artefacto | Método de verificación |
|-----------|------------------------|
| Especificación (`PROJECT.md`, `REQUIREMENTS.md`) | Revisión manual: los 5 resultados, las reglas de negocio, los criterios de aceptación y el caso de referencia aparecen íntegros |
| Seed de datos | Recálculo manual de los 8 escenarios: cada uno alcanza su `expected_outcome`. Disponibilidades verificadas (`on_hand − reserved`) contra las cantidades solicitadas |
| Reglas de negocio | Cada `BR-xx` tiene al menos un criterio de aceptación (`AC-xx`) y un test asociado; la tabla de `REQUIREMENTS.md` §5 es la matriz de trazabilidad |
| Código de dominio y grafo | `pytest` sin LLM externo + `ruff` + `mypy` sobre `app/domain` y `app/graph/state.py` — incluido el trabajo producido por sesiones delegadas, verificado por la sesión principal antes de aceptarlo |
| Reanudación e idempotencia | T13 descarta y reconstruye grafo y checkpointer entre interrumpir y reanudar (reinicio real, no solo del mismo objeto). T14 reenvía el mismo `decision_id` vía `OBSERVE` (la única acción que mantiene el caso en pausa) para verificar BR-15 sobre un grafo que sigue vivo. Ver `EVIDENCE.md` E-09 |
| Coherencia docs ↔ código | Revisión al cierre de cada fase: `STATE.md` y `EVIDENCE.md` se actualizan con comandos ejecutados y su salida real, no con lo esperado |

## 4. Límites del registro

- Este documento se actualiza al cierre de cada fase, no al final del proyecto.
- Lo que no se verificó se declara como tal en `EVIDENCE.md` bajo "limitaciones", en lugar de presentarse como verificado.
- Ningún resultado de prueba se reporta aquí sin su comando y salida en `EVIDENCE.md`.

---

**Relacionados:** [ADR-001](../adr/ADR-001-datos-ficticios-propios.md) · [ADR-002](../adr/ADR-002-frontera-determinista.md) · [STATE.md](STATE.md) · [EVIDENCE.md](EVIDENCE.md) · [docs/REFERENCES.md](../REFERENCES.md)
