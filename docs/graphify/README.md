# Graphify: mapa estructural del backend

Graphify extrae del código de `backend/app/` un grafo de módulos, clases y funciones. Lo hace analizando el AST con tree-sitter, de forma local y sin costo de API, y agrupa los nodos en comunidades. Este directorio guarda el resultado versionado:

| Archivo | Contenido |
|---------|-----------|
| [GRAPH_REPORT.md](GRAPH_REPORT.md) | Resumen: nodos más conectados, comunidades, conexiones inesperadas, ciclos de import |
| `graph.json` | El grafo completo, para consultarlo con `graphify path` / `graphify explain` |
| `graph.html` | Visualización interactiva (abrir en el navegador) |

La lectura de negocio de este mapa está en [IMPACT.md](../IMPACT.md) §3.

## Regenerarlo

Se regenera **al cerrar cada fase**, o cuando un cambio agrega o mueve módulos. Requiere `graphifyy` (`uv tool install graphifyy`). Desde la raíz del repo:

```bash
graphify extract backend/app --code-only
graphify cluster-only backend/app
cp backend/app/graphify-out/{GRAPH_REPORT.md,graph.json,graph.html} docs/graphify/
rm -rf backend/app/graphify-out
```

`graphify-out/` está en `.gitignore`: solo se versiona la copia en `docs/graphify/`.

**Comprobación de la frontera de ADR-002**, después de regenerar:

```bash
cd backend
grep -rn "from app\.\(llm\|graph\|api\)" app/domain   # debe estar vacío
grep -rhn "from app\.domain" app/llm                 # solo models (Extraction, ExtractedLineItem)
```

## Historia

| Momento | Archivos | Nodos | Aristas | Comunidades | Ciclos de import |
|---------|---------:|------:|--------:|------------:|------------------|
| Fase 1 (dominio y grafo) | 26 | 199 | 403 | 16 | ninguno |
| Fase 2-3 (con `app/api/`) | 31 | 265 | 588 | 15 | ninguno |
| Antes de la Fase 4 | 33 | 289 | 622 | 17 | ninguno |
| **Fase 4 (v0.5.x)** | **36** | **326** | **703** | **17** | **ninguno** |

### Qué cambió con la Fase 4

| Módulo | Nodos antes → después | Qué es |
|--------|----------------------:|--------|
| `llm/gemini_extractor.py` | 0 → 13 | Extractor con Gemini: esquema, errores del proveedor, anotación de la traza |
| `llm/fallback.py` | 0 → 7 | Respaldo al extractor de reglas cuando el proveedor no responde |
| `domain/manipulation.py` | 0 → 5 | Detector determinista de BR-18; forma su propia comunidad |
| `graph/nodes.py` | 28 → 31 | El nodo `extract` integra el detector y la señal del LLM |
| `api/routes.py` | 14 → 16 | Nombres y metadatos de las trazas por solicitud |
| `config.py` | 4 → 6 | Configuración de Gemini y de LangSmith |

- **`Extraction` sube al top 10** de nodos más conectados (15 → 21 aristas) y da nombre a la comunidad de la capa LLM: ahora la usan tres extractores y el respaldo.
- **`QuoteState` sigue siendo el nodo central** (38 → 40 aristas).
- **`NodeFn` aparece con 16 aristas.** Es un efecto del cambio de tipos de v0.5.1: pasó de alias a `Protocol` (una clase), y Graphify infiere relaciones de "uso" para las clases. No refleja un acoplamiento nuevo; el código de los nodos no cambió.
- **Sigue sin haber ciclos de import**, y ninguna arista va de `llm/` a reglas del dominio (política, precios, inventario).
