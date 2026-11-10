# Graph Report - backend\app  (2026-11-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 326 nodes · 703 edges · 17 communities
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 199 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `39284917`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Extraction
- QuoteState
- Tier
- lifespan
- ReasonCode
- create_request
- store.py
- tools.py
- PolicyEvaluation
- calculate_quote
- classify_decision
- manipulation.py

## God Nodes (most connected - your core abstractions)
1. `QuoteState` - 40 edges
2. `ReasonCode` - 32 edges
3. `DecisionAction` - 29 edges
4. `AuditEvent` - 24 edges
5. `Outcome` - 22 edges
6. `Tier` - 21 edges
7. `Extraction` - 21 edges
8. `ApprovalReason` - 16 edges
9. `NodeFn` - 16 edges
10. `to_request_detail()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `decide_request()` --calls--> `classify_decision()`  [INFERRED]
  api/routes.py → domain/decisions.py
- `NodeFn` --uses--> `Outcome`  [INFERRED]
  graph/nodes.py → domain/enums.py
- `AuditEvent` --uses--> `Outcome`  [INFERRED]
  graph/state.py → domain/enums.py
- `QuoteState` --uses--> `Outcome`  [INFERRED]
  graph/state.py → domain/enums.py
- `NodeFn` --uses--> `ReasonCode`  [INFERRED]
  graph/nodes.py → domain/enums.py

## Import Cycles
- None detected.

## Communities (17 total, 0 thin omitted)

### Community 0 - "Extraction"
Cohesion: 0.06
Nodes (41): AsyncClient, Extraction, Salida estructurada del LLM (RF-05). `extra="ignore"` es la sanitizacion de…, Exception, `fake`: extractor de reglas, sin red (tests y demo sin key). `real` + `gemini`:…, _resolve_extractor(), ExtractionError, Extractor (+33 more)

### Community 1 - "QuoteState"
Cohesion: 0.07
Nodes (51): apply_decision(), check_inventory(), compose_draft(), evaluate_policy(), finalize(), human_approval(), ingest(), make_extract_node() (+43 more)

### Community 2 - "Tier"
Cohesion: 0.08
Nodes (41): Nivel comercial del cliente. Determina el descuento maximo autorizado., Tier, ApprovalReason, Customer, DiscountTierPolicy, ExtractedLineItem, HumanDecision, InventoryRecord (+33 more)

### Community 3 - "lifespan"
Cohesion: 0.08
Nodes (28): AbstractEventLoop, AsyncConnectionPool, AsyncPostgresSaver, BaseCheckpointSaver, BaseSettings, CompiledStateGraph, configure_tracing(), get_settings() (+20 more)

### Community 4 - "ReasonCode"
Cohesion: 0.17
Nodes (30): is_paused(), _line_subtotal(), _money(), Decimal, Traduce `QuoteState` (dominio/grafo) + la fila de cache (store.py) a los…, Recalculo de presentacion (RF-06): ResolvedLine no persiste el subtotal de…, BLOCKED puede venir de BR-12/13 (`blocking_reason`); NEEDS_CLARIFICATION puede…, resolve_blocking_reason() (+22 more)

### Community 5 - "create_request"
Cohesion: 0.17
Nodes (22): Resumen corto para la bandeja, ej. '20 x HX-200'., `PENDING_APPROVAL` es un estado observado (el grafo esta pausado), no algo que…, resolve_outcome(), summarize(), _config(), create_request(), _current_state(), decide_request() (+14 more)

### Community 6 - "store.py"
Cohesion: 0.13
Nodes (21): get(), get_for_update(), insert(), list_all(), Any, Almacen de metadatos de solicitudes (bandeja) sobre Postgres (ADR-003). La…, Bloquea la fila hasta el fin de la transaccion: serializa las decisiones sobre…, Crea la tabla si no existe. Se corre una sola vez, en el lifespan (CLAUDE.md… (+13 more)

### Community 7 - "tools.py"
Cohesion: 0.16
Nodes (16): _catalog_repo(), check_availability(), _customer_repo(), get_policy(), get_unit_price(), _inventory_repo(), lookup_customer(), lookup_product() (+8 more)

### Community 8 - "PolicyEvaluation"
Cohesion: 0.24
Nodes (7): evaluate_policy(), PolicyEvaluation, BaseModel, Decimal, Motor de politica comercial (BR-05..BR-09). Decide si una cotizacion pasa…, Resultado de evaluar una cotizacion contra la politica comercial. `rejection`…, `tier` ya viene resuelto por el caller: BR-08 exige STANDARD provisional cuando…

### Community 9 - "calculate_quote"
Cohesion: 0.43
Nodes (6): calculate_quote(), Decimal, Motor de precios determinista (RF-06, BR-04). No decide nada: recibe lineas ya…, BR-04: ROUND_HALF_UP explicito -- el default de Decimal es ROUND_HALF_EVEN., RF-06: subtotal por linea -> subtotal total -> descuento -> neto -> IGV ->…, _round()

### Community 10 - "classify_decision"
Cohesion: 0.40
Nodes (5): classify_decision(), DecisionVerdict, StrEnum, Clasificacion de una decision humana entrante (BR-15, BR-19). Funcion pura: la…, BR-15: reenviar la misma decision no tiene efecto. BR-19: una decision que…

### Community 11 - "manipulation.py"
Cohesion: 0.50
Nodes (4): detect_manipulation(), _normalize(), Deteccion determinista de intentos de manipulacion en el texto del cliente.…, Etiquetas de los patrones encontrados, en orden; vacia si no hay ninguno.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QuoteState` connect `QuoteState` to `Extraction`, `Tier`, `ReasonCode`, `create_request`?**
  _High betweenness centrality (0.281) - this node is a cross-community bridge._
- **Why does `Extraction` connect `Extraction` to `QuoteState`, `Tier`, `ReasonCode`?**
  _High betweenness centrality (0.231) - this node is a cross-community bridge._
- **Why does `_resolve_extractor()` connect `Extraction` to `lifespan`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `QuoteState` (e.g. with `NodeFn` and `Outcome`) actually correct?**
  _`QuoteState` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `ReasonCode` (e.g. with `ApprovalReasonOut` and `AuditEventOut`) actually correct?**
  _`ReasonCode` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `DecisionAction` (e.g. with `ApprovalReasonOut` and `AuditEventOut`) actually correct?**
  _`DecisionAction` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `AuditEvent` (e.g. with `apply_decision()` and `check_inventory()`) actually correct?**
  _`AuditEvent` has 21 INFERRED edges - model-reasoned connections that need verification._