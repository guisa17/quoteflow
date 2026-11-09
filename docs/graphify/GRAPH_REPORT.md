# Graph Report - app  (2026-11-09)

## Corpus Check
- 33 files · ~10,349 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 289 nodes · 622 edges · 17 communities
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 177 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Regenerated on 2026-11-09.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Tier
- QuoteState
- ReasonCode
- build_graph
- FakeExtractor
- store.py
- create_request
- tools.py
- PolicyEvaluation
- calculate_quote
- classify_decision
- prompts.py

## God Nodes (most connected - your core abstractions)
1. `QuoteState` - 38 edges
2. `ReasonCode` - 31 edges
3. `DecisionAction` - 28 edges
4. `AuditEvent` - 23 edges
5. `Outcome` - 21 edges
6. `Tier` - 20 edges
7. `to_request_detail()` - 15 edges
8. `Policy` - 15 edges
9. `Extraction` - 15 edges
10. `ApprovalReason` - 15 edges

## Surprising Connections (you probably didn't know these)
- `decide_request()` --calls--> `classify_decision()`  [INFERRED]
  api/routes.py → domain/decisions.py
- `AuditEvent` --uses--> `Outcome`  [INFERRED]
  graph/state.py → domain/enums.py
- `QuoteState` --uses--> `Outcome`  [INFERRED]
  graph/state.py → domain/enums.py
- `AuditEvent` --uses--> `ReasonCode`  [INFERRED]
  graph/state.py → domain/enums.py
- `QuoteState` --uses--> `ReasonCode`  [INFERRED]
  graph/state.py → domain/enums.py

## Import Cycles
- None detected.

## Communities (17 total, 0 thin omitted)

### Community 0 - "Tier"
Cohesion: 0.08
Nodes (43): Nivel comercial del cliente. Determina el descuento maximo autorizado., Tier, ApprovalReason, Customer, DiscountTierPolicy, ExtractedLineItem, Extraction, HumanDecision (+35 more)

### Community 1 - "QuoteState"
Cohesion: 0.08
Nodes (46): apply_decision(), check_inventory(), compose_draft(), evaluate_policy(), finalize(), human_approval(), ingest(), price_quote() (+38 more)

### Community 2 - "ReasonCode"
Cohesion: 0.16
Nodes (32): is_paused(), _line_subtotal(), _money(), Decimal, Traduce `QuoteState` (dominio/grafo) + la fila de cache (store.py) a los…, Recalculo de presentacion (RF-06): ResolvedLine no persiste el subtotal de…, `PENDING_APPROVAL` es un estado observado (el grafo esta pausado), no algo que…, BLOCKED puede venir de BR-12/13 (`blocking_reason`); NEEDS_CLARIFICATION puede… (+24 more)

### Community 3 - "build_graph"
Cohesion: 0.08
Nodes (28): AbstractEventLoop, AsyncConnectionPool, AsyncPostgresSaver, BaseCheckpointSaver, BaseSettings, CompiledStateGraph, get_settings(), Settings (+20 more)

### Community 4 - "FakeExtractor"
Cohesion: 0.10
Nodes (20): Exception, make_extract_node(), RF-05: un intento de extraccion por invocacion de este nodo. El reintento (una…, ExtractionError, Extractor, Frontera del LLM (ADR-002, T8). Protocolo minimo que cualquier extractor --…, El extractor no pudo producir una `Extraction` valida. Cubre tanto un esquema…, Contrato compartido por el extractor fake (T8) y el real (LOOP.md). (+12 more)

### Community 5 - "store.py"
Cohesion: 0.13
Nodes (21): get(), get_for_update(), insert(), list_all(), Any, Almacen de metadatos de solicitudes (bandeja) sobre Postgres (ADR-003). La…, Bloquea la fila hasta el fin de la transaccion: serializa las decisiones sobre…, Crea la tabla si no existe. Se corre una sola vez, en el lifespan (CLAUDE.md… (+13 more)

### Community 6 - "create_request"
Cohesion: 0.21
Nodes (18): Resumen corto para la bandeja, ej. '20 x HX-200'., summarize(), _config(), create_request(), _current_state(), decide_request(), get_request(), list_requests() (+10 more)

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

### Community 11 - "prompts.py"
Cohesion: 0.50
Nodes (3): build_messages(), Instrucciones de extraccion para el extractor real (BR-17, ADR-002).…, Arma los mensajes para el extractor real (BR-17). `raw_text` se delimita…

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QuoteState` connect `QuoteState` to `Tier`, `ReasonCode`, `create_request`?**
  _High betweenness centrality (0.303) - this node is a cross-community bridge._
- **Why does `Extraction` connect `Tier` to `QuoteState`, `ReasonCode`, `FakeExtractor`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `_resolve_extractor()` connect `build_graph` to `FakeExtractor`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `QuoteState` (e.g. with `Outcome` and `ReasonCode`) actually correct?**
  _`QuoteState` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `ReasonCode` (e.g. with `ApprovalReasonOut` and `AuditEventOut`) actually correct?**
  _`ReasonCode` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `DecisionAction` (e.g. with `ApprovalReasonOut` and `AuditEventOut`) actually correct?**
  _`DecisionAction` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `AuditEvent` (e.g. with `apply_decision()` and `check_inventory()`) actually correct?**
  _`AuditEvent` has 20 INFERRED edges - model-reasoned connections that need verification._