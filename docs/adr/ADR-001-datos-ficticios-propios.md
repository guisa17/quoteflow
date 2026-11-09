# ADR-001 — Datos de dominio ficticios y versionados

- **Estado:** Aceptada
- **Fecha:** 2026-08-04
- **Decisor:** Guillermo Salcedo
- **Afecta a:** `backend/app/data/*.json`, dominio determinista, suite de pruebas, evidencia

---

## Contexto

Sin datos de dominio no hay nada que validar: las reglas de negocio (umbral de USD 10 000, máximos de descuento por nivel, stock, cliente desconocido) son inertes sin un catálogo, un inventario, un padrón de clientes y una política concretos. QuoteFlow no se conecta a un ERP real, así que esos datos tienen que existir dentro del proyecto.

## Decisión

**Se crea un seed ficticio propio, versionado en Git**, dimensionado al mínimo necesario para ejercitar los cinco resultados del sistema. La empresa Ferrocima Industrial y sus clientes son ficticios. El caso de referencia es:

> "Necesito 20 cascos modelo HX-200 para la planta de Arequipa. Somos clientes Gold. Requiero entrega la próxima semana y un 8% de descuento."

El seed consta de:

| Archivo | Contenido | Dimensionamiento |
|---------|-----------|------------------|
| `customers.json` | `FER-1001` GOLD · `FER-1002` SILVER · `FER-1003` STANDARD | 3 niveles ⇒ 3 filas de política de descuento, suficiente para probar excepción y cumplimiento |
| `products.json` | 6 SKU de EPP con precio de lista | Uno por categoría de protección |
| `inventory.json` | `on_hand` / `reserved` por SKU | Separado del catálogo porque responden a consultas distintas |
| `policies.json` | Máximos por nivel, techo duro, umbral, IGV | Las reglas comerciales, parametrizadas |
| `sample_requests.json` | 8 escenarios con resultado esperado | Cubre los 5 resultados + inyección de prompt |

Los valores están **calibrados** para que cada resultado del sistema sea alcanzable con un escenario del seed y para que el caso de referencia termine en `DRAFT_READY` (900.00 → 8 % ≤ 12 % GOLD → neto 828.00 < 10 000).

## Alternativas consideradas

| Alternativa | Descartada porque |
|-------------|-------------------|
| Generar el seed con el LLM en tiempo de ejecución | Contradice frontalmente BR-01 y BR-03: el modelo no puede producir datos de dominio. Además destruye la reproducibilidad de las pruebas |
| Datos aleatorios o genéricos (`Producto 1`, `Cliente A`) | No permiten reconocer si el sistema aplica correctamente la política: un caso sin significado comercial no se puede verificar manualmente |
| Un seed grande y "realista" (cientos de SKU) | Coste sin retorno: importan el criterio y la verificabilidad, no el volumen. Un seed pequeño y calibrado se audita a mano en minutos |

## Consecuencias

**Positivas**

- Las pruebas son deterministas y reproducibles byte a byte: el seed está en Git.
- Cada criterio de aceptación tiene un escenario asociado y cifras verificables a mano.
- Cualquier persona puede recalcular una cotización con una calculadora y contrastar.

**Negativas / riesgos asumidos**

- **El seed no refleja un negocio real.** Cualquier conclusión sobre márgenes o rotación es ilustrativa. Mitigación: el acceso a datos está tras repositorios (`CustomerRepository`, `CatalogRepository`, `InventoryRepository`, `PolicyRepository`) sustituibles por una fuente real sin tocar el grafo ni las reglas.
- **Los valores de política son inventados** (12 / 8 / 5 %, techo 20 %, umbral USD 10 000). Mitigación: todos viven en `policies.json`, no en el código; cambiarlos es editar un archivo — ver `IMPACT.md`.
