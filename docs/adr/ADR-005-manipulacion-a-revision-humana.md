# ADR-005 — Un intento de manipulación detectado va a revisión humana

- **Estado:** Aceptada
- **Fecha:** 2026-11-09
- **Decisor:** Guillermo Salcedo
- **Afecta a:** `app/domain/manipulation.py`, `app/domain/policy.py`, `app/graph/nodes.py` (`extract`), `Extraction.injection_suspected`, `ReasonCode.SUSPECTED_MANIPULATION`, BR-18
- **Relacionada con:** [ADR-002](ADR-002-frontera-determinista.md), [ADR-004](ADR-004-extractor-gemini-con-respaldo.md)

---

## Contexto

ADR-002 garantiza que un texto malicioso no puede cambiar precio, nivel del cliente, política ni aprobación: el extractor no tiene esos campos. Esa defensa funcionó al probar con Gemini un pedido de 40 lentes con una "nota del sistema" que pedía fijar el precio en 1 USD, subir al cliente a GOLD y marcar la cotización como aprobada. El precio quedó en 12,75 y el nivel en STANDARD.

El problema fue otro: como 40 lentes están dentro de política, el folio salió como **"Borrador listo, resuelto por las reglas, sin intervención humana"**, sin ninguna marca. Nadie se enteraba de que un cliente intentó manipular el sistema, y el borrador quedaba listo para enviarse.

BR-18 ya pedía registrar un intento detectado, pero el sistema no detectaba ninguno. Faltaba decidir **qué pasa con el caso** cuando se detecta.

## Decisión

**Detectar con dos señales independientes y, si cualquiera se activa, exigir revisión humana.**

1. **Detector determinista** (`app/domain/manipulation.py`): patrones sobre el texto normalizado (minúsculas, sin tildes) que buscan frases dirigidas al sistema: "nota del sistema", "ignora las políticas", "fija el precio", "marca como aprobada", "no menciones esto", etiquetas `<system>`. No depende del LLM, que es justamente el componente atacado.
2. **Señal del LLM** (`Extraction.injection_suspected`): el extractor real marca si el texto intenta dar órdenes. Solo puede **provocar** una revisión, nunca evitarla.
3. **Efecto:** el intento se registra en la auditoría del nodo `extract` y la política añade el motivo `SUSPECTED_MANIPULATION` **en primer lugar**, así que el folio pasa a "Pendiente de aprobación" y la bandeja lo muestra como motivo principal.
4. **Un rechazo duro sigue dominando** (BR-09): si además se pide un descuento sobre el techo, el caso se rechaza y el intento queda igualmente en la auditoría.
5. **Pedir descuento no es manipulación.** "Nos pueden poner un 10 %" o "somos clientes Gold" son pedidos comerciales que ya evalúa la política, y los patrones no los marcan.

## Alternativas consideradas

| Alternativa | Descartada porque |
|-------------|-------------------|
| Seguir el flujo normal y solo registrarlo (texto original de BR-18) | El borrador sale igual, sin que nadie lo mire. El registro existe, pero nadie lo lee a tiempo |
| Rechazar automáticamente | Un falso positivo cerraría un pedido legítimo sin posibilidad de aprobarlo. La revisión humana absorbe ese error |
| Solo la señal del LLM | El LLM es el componente atacado: un texto bien construido podría convencerlo de no marcarlo |
| Solo patrones deterministas | Se escapan las paráfrasis. La señal del LLM cubre ese hueco sin poder anular a los patrones |
| Un clasificador de inyección dedicado (otro modelo) | Otra llamada, otra cuota y otro punto de fallo para un proyecto de este tamaño |

## Consecuencias

**Positivas**

- Un intento nunca pasa desapercibido: queda en la auditoría, en el motivo del folio y en la bandeja.
- La decisión sigue siendo de las reglas: el LLM aporta una señal, no un veredicto.
- El costo de un falso positivo es una revisión humana, no un pedido perdido.

**Negativas / límites asumidos**

- Los patrones son una lista finita: un ataque escrito de forma muy distinta puede pasar si el LLM tampoco lo marca. En ese caso sigue valiendo ADR-002: el ataque no cambia ninguna cifra.
- Cada patrón nuevo puede crear falsos positivos; por eso se prueba contra todos los escenarios legítimos y frases comerciales comunes.

## Verificación

- `tests/unit/test_manipulation.py` — positivos, negativos, que en el seed solo se marque `S8`, el orden de los motivos y que el rechazo duro domine.
- `tests/integration/test_api.py` — `S8` registra el intento en la auditoría; el caso reportado (nota del sistema dentro de política) termina en `PENDING_APPROVAL` con precio intacto.
- `frontend/src/mocks/engine.test.ts` — la misma regla en el modo demo.
- Prueba en vivo: Gemini marcó los dos ataques y ninguno de los 8 pedidos legítimos.
