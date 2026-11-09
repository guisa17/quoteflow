# BUSINESS_CASE — QuoteFlow (Ferrocima Industrial)

> Caso de negocio del MVP. Máx. 2 páginas.
> Todas las cifras de línea base están marcadas como **supuesto** — son ficticias y deben validarse en el piloto.

---

## 1. Usuario y proceso actual

**Usuario primario:** ejecutivo comercial de Ferrocima (perfil "inside sales"), responsable de responder solicitudes de cotización de equipamiento de protección personal (EPP) industrial.
**Usuario secundario:** jefe comercial, que autoriza excepciones de descuento y operaciones de monto alto.

El proceso actual, por solicitud, es enteramente manual:

| # | Paso | Herramienta hoy |
|---|------|-----------------|
| 1 | Leer texto libre (correo, formulario, WhatsApp) | Bandeja de entrada |
| 2 | Identificar al cliente y su nivel comercial | ERP / hoja de cálculo |
| 3 | Interpretar productos, cantidades, sede, fecha | Criterio propio |
| 4 | Verificar catálogo, precio vigente y stock | ERP / inventario |
| 5 | Aplicar política de descuento por nivel | Manual comercial (PDF) |
| 6 | Escalar excepciones al jefe comercial | Correo / mensajería |
| 7 | Redactar y enviar el borrador | Plantilla Word |

**Supuesto de trabajo:** 20–35 min por cotización, ~40 solicitudes/semana, ~15 % requieren escalamiento. A validar en el piloto.

## 2. Problema

El cuello de botella no es redactar: es **reconstruir el contexto** (paso 2–5) en cada solicitud. Eso produce tres costos:

- **Latencia comercial.** El tiempo de respuesta compite directamente con distribuidores rivales; una cotización tardía se pierde antes de ser evaluada.
- **Fuga de margen.** Los descuentos se aplican por memoria y presión del cliente, no contra una tabla. Las excepciones no dejan rastro auditable.
- **Compromisos no servibles.** Se cotiza sobre stock que no está disponible, generando reprogramaciones y pérdida de confianza.

## 3. Hipótesis de valor

> Si un sistema interpreta la solicitud y **precalcula** la cotización contra los datos vigentes de catálogo, inventario y política —dejando la decisión final en manos humanas—, el ejecutivo pasa de **redactar desde cero** a **revisar y confirmar**, reduciendo el tiempo por cotización y eliminando los descuentos fuera de política aplicados sin registro.

El sistema no reemplaza el criterio comercial: reparte el trabajo en tres capas con responsabilidades separadas —el modelo interpreta el texto, el dominio calcula, la persona decide—. El valor depende de que esa frontera esté delimitada con precisión, y por eso es el objeto de [ADR-002](docs/adr/ADR-002-frontera-determinista.md).

## 4. MVP

Un ejecutivo registra una solicitud en lenguaje natural, el sistema la procesa por un workflow con estado explícito, y la solicitud termina en **uno** de cinco resultados observables:

| Resultado | Cuándo |
|-----------|--------|
| `NEEDS_CLARIFICATION` | Falta información esencial (p. ej. cantidad) |
| `DRAFT_READY` | Todo válido y dentro de política |
| `BLOCKED` | Stock insuficiente o SKU inexistente |
| `PENDING_APPROVAL` | Monto > USD 10 000, excepción de descuento, o cliente desconocido |
| `REJECTED_BY_POLICY` | Descuento sobre el techo duro (20 %) |

El MVP **prepara borradores; no envía nada al cliente.**

### No alcance (explícito)

Fuera por decisión, no por falta de tiempo:

- **Envío automático al cliente** — contradice el nivel de autonomía elegido (§7).
- Autenticación empresarial / SSO y roles finos. Se asume un ejecutivo confiable en sesión.
- Integraciones reales con correo, WhatsApp o ERP. Los datos de dominio se leen de un seed local versionado.
- Facturación, órdenes de compra, reserva efectiva de stock.
- Escalas de precio por volumen y negociación multironda. Una sola dimensión de descuento (comercial por nivel) para mantener el cálculo auditable.
- Infraestructura productiva (HA, autoescalado) y diseño visual avanzado.

## 5. Métricas

**De éxito** (¿funciona?)

| Métrica | Línea base (supuesto) | Objetivo piloto |
|---------|----------------------|-----------------|
| Tiempo medio solicitud → borrador revisado | 20–35 min | ≤ 8 min |
| Cotizaciones sin retrabajo del ejecutivo | — | ≥ 70 % |
| Extracción correcta de SKU + cantidad | — | ≥ 90 % |

**De guardia** (¿es seguro?) — una sola de estas en rojo detiene la expansión del piloto:

| Métrica | Umbral |
|---------|--------|
| Cotizaciones emitidas con descuento fuera de política | **0** (bloqueante) |
| Precios, stock o clientes inventados por el modelo | **0** (bloqueante) |
| Aprobaciones con efecto duplicado | **0** (bloqueante) |
| Solicitudes cotizadas sin la info esencial | ≤ 2 % |
| Falsos bloqueos (frenó algo que era válido) | ≤ 10 % |

Nota de diseño: es preferible un falso bloqueo que una cotización errónea. Las guardias son asimétricas a propósito.

## 6. Riesgos principales

| Riesgo | Impacto | Mitigación en el MVP |
|--------|---------|----------------------|
| El LLM alucina SKU, precio o stock | Alto | El LLM **solo extrae y redacta**. Todo cálculo y validación vive en funciones deterministas del dominio; un SKU no presente en catálogo bloquea el caso ([ADR-002](docs/adr/ADR-002-frontera-determinista.md)) |
| Inyección de prompt en el texto del cliente | Alto | El texto se trata como dato, nunca como instrucción. Las políticas se leen de configuración del sistema, no del mensaje. Caso de prueba dedicado (`S8`) |
| Doble efecto de una misma aprobación | Medio | Decisión humana idempotente por `(thread_id, decision_id)`; reintentos convergen al mismo estado |
| Pérdida de estado ante reinicio | Medio | Checkpointer persistente en PostgreSQL; una ejecución interrumpida se reanuda tras reiniciar la app |
| Exceso de confianza del ejecutivo ("automation bias") | Medio | La UI muestra la trazabilidad (qué se extrajo, qué regla se aplicó) junto al borrador, no solo el resultado |
| Datos de dominio ficticios ≠ realidad de Ferrocima | Medio | Documentado como supuesto ([ADR-001](docs/adr/ADR-001-datos-ficticios-propios.md)); las fuentes de datos están tras una interfaz reemplazable |

## 7. Nivel de autonomía recomendado

**Nivel 2 de 4 — "propone y espera confirmación".**

| Nivel | Descripción | ¿Aquí? |
|-------|-------------|--------|
| 0 | Solo sugiere texto | Insuficiente: no captura el valor del cálculo |
| 1 | Precalcula, el humano rehace todo | Insuficiente: no reduce tiempo |
| **2** | **Precalcula, valida y prepara borrador; el humano aprueba y envía** | **Recomendado** |
| 3 | Envía automáticamente los casos dentro de política | No en el MVP |
| 4 | Negocia y cierra | No aplica a este caso |

Razón: el costo de un error es asimétrico. Un descuento mal aplicado o un compromiso de stock inexistente daña margen y relación comercial de forma difícil de revertir, mientras que el costo de una confirmación humana es de segundos. El nivel 3 solo debería evaluarse tras el piloto y únicamente para el subconjunto `DRAFT_READY` con cero incidentes de guardia.

## 8. Propuesta de piloto

- **Duración:** 3 semanas.
- **Alcance:** 1 ejecutivo comercial, línea EPP, los 3 clientes del seed + clientes reales cargados a mano.
- **Modo:** *shadow* la semana 1 (el sistema propone, el ejecutivo compara contra su propio proceso y registra discrepancias), asistido las semanas 2–3.
- **Criterio de continuidad:** las tres métricas de guardia bloqueantes en cero y tiempo medio ≤ 8 min.
- **Criterio de corte:** una sola cotización emitida con descuento fuera de política detiene el piloto y abre revisión de la frontera determinista.
- **Siguiente decisión (post-piloto):** integrar la fuente real de inventario del ERP, o ampliar a una segunda línea de producto — no ambas a la vez.

---

**Documentos relacionados:** [PROJECT.md](PROJECT.md) · [REQUIREMENTS.md](REQUIREMENTS.md) · [ADR-001](docs/adr/ADR-001-datos-ficticios-propios.md) · [ADR-002](docs/adr/ADR-002-frontera-determinista.md) · [STATE.md](STATE.md)
