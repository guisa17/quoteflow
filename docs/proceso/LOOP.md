# LOOP — Ciclo acotado de mejora

> **Documento histórico.** Este ciclo se diseñó para construir el extractor real y nunca llegó a ejecutarse tal cual. El extractor se construyó después con Gemini (`backend/app/llm/gemini_extractor.py`), sobre el mismo contrato y con el mismo verifier (los 8 escenarios), más casos en lenguaje natural. El resultado y los hallazgos están en [ROADMAP.md](../ROADMAP.md) (Fase 4).

Un solo loop, con presupuesto y condición de salida explícitos. No es un plan de trabajo general (eso vive en `ROADMAP.md` / `PHASE_01.md`): es el ciclo de **corrección iterativa** sobre el punto más frágil del sistema.

---

## Por qué este loop y no otro

La arquitectura ([ADR-002](../adr/ADR-002-frontera-determinista.md)) concentra deliberadamente toda la incertidumbre en un solo lugar: **la extracción**. El dominio es determinista y se prueba con aserciones exactas; el routing es comparación de valores tipados. Si algo va a fallar de forma no reproducible, falla en el paso texto libre → `Extraction`.

Por eso el único loop que merece presupuesto es el que endurece esa frontera. El resto del trabajo es lineal y no necesita iterar.

---

## Definición del loop

### Objetivo

Que los **8 escenarios** de [`sample_requests.json`](../../backend/app/data/sample_requests.json) alcancen su `expected_outcome` y `expected_reason`, ejecutando el grafo completo con el extractor real (`LLM_MODE=real`), sin relajar ninguna regla de `REQUIREMENTS.md` §2 para conseguirlo.

Medida única y binaria: **8/8 en verde**.

### Worker

Claude Code, con alcance restringido a tres archivos:

- `backend/app/llm/prompts.py` — instrucciones de extracción
- `backend/app/llm/anthropic_extractor.py` — esquema de salida y saneamiento
- `backend/app/graph/nodes.py` (solo el nodo `extract`) — degradación ante fallo

**Prohibido al worker:** tocar `app/domain/`, `policies.json`, los `expected_outcome` de los escenarios, o cualquier umbral. Si el loop necesita cambiar una regla para pasar, el loop ha fallado — la regla es la especificación, no la variable de ajuste.

### Verifier

Independiente del worker, sin criterio propio:

```bash
cd backend
LLM_MODE=real uv run pytest tests/integration/test_scenarios.py -v
LLM_MODE=fake uv run pytest                     # no debe romperse nada más
uv run mypy app/domain app/graph/state.py
```

El verifier no interpreta: si un test falla, el ciclo no avanza. La salida real de estos comandos se pega en `EVIDENCE.md`.

### Presupuesto

**3 iteraciones.** Una iteración = un cambio en los archivos del worker + una ejecución completa del verifier.

El presupuesto se cuenta en iteraciones y no en tiempo, porque lo que degrada este ciclo es insistir sobre el mismo diagnóstico, no su duración. Es duro: al agotarse se aplica la condición de bloqueo, no se extiende.

### Condición de salida (éxito)

- 8/8 escenarios en verde con `LLM_MODE=real`, **y**
- la suite completa en verde con `LLM_MODE=fake`, **y**
- ninguna regla, umbral ni `expected_outcome` modificado durante el loop.

### Condición de bloqueo (fracaso controlado)

Se dispara si al agotar las 3 iteraciones **el mismo escenario sigue fallando**.

Acción, en este orden:

1. **No se fuerza el paso.** No se ajusta el escenario ni la regla para que pase.
2. El nodo `extract` degrada ese caso a `NEEDS_CLARIFICATION` con `EXTRACTION_FAILED` — el comportamiento seguro ya especificado en RF-05. Un caso que el sistema no entiende **pregunta**; no adivina.
3. Se registra en `EVIDENCE.md` bajo *limitaciones*: qué escenario, qué extrajo el modelo, qué se esperaba.
4. Se registra en `AI_USE.md` §3 como output rechazado.
5. El loop termina. No se abre un segundo loop sobre el mismo objetivo dentro de esta fase.

### Handoff

Al cerrar (por éxito o por bloqueo), en el mismo ciclo:

- `EVIDENCE.md` ← comandos ejecutados y **salida real**, iteraciones consumidas, limitaciones.
- `STATE.md` ← estado y siguiente paso.
- `AI_USE.md` ← outputs aceptados/rechazados de este loop.
- Commit atómico con el resultado del loop, en verde o con la limitación documentada.

Quien retome el proyecto debe poder responder, solo con esos archivos: *¿qué se intentó, cuántas veces, qué quedó fuera y por qué*.

---

## Estado

| Campo | Valor |
|-------|-------|
| **Estado** | ⬜ **Decidido no ejecutar** — ver justificación abajo |
| **Iteraciones consumidas** | 0 / 3 |
| **Escenarios en verde** | — / 8 |
| **Bloqueo disparado** | No |

### Por qué no se ejecuta

`app/llm/` y `tests/integration/test_scenarios.py` ya existen (Fase 1 completa) — el ciclo es técnicamente ejecutable. No se ejecuta por decisión, no por bloqueo:

- `LLM_MODE=fake` permite verificar todo el flujo sin un modelo externo; el extractor real se puede construir después sin tocar el dominio.
- Construir `anthropic_extractor.py` implica credenciales, manejo de errores de proveedor real y presupuesto adicional no trivial.
- El tiempo restante rinde más en `app/api/` y en el cierre (Fase 3) .

Si en algún momento se decide ejecutarlo (por ejemplo, para tener un camino con LLM real demostrable en la presentación), la definición de arriba sigue vigente sin cambios.

### Bitácora

| # | Fecha | Cambio aplicado | Resultado del verifier |
|---|-------|-----------------|------------------------|
| — | — | *(no ejecutado — ver "Por qué no se ejecuta")* | — |

---

**Relacionados:** [EVIDENCE.md](EVIDENCE.md) · [AI_USE.md](AI_USE.md) · [ADR-002](../adr/ADR-002-frontera-determinista.md) · [CLAUDE.md](../../CLAUDE.md)
