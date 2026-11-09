---
name: QuoteFlow
description: Consola de cotización B2B con lenguaje editorial sobrio; el agente propone y una persona decide.
colors:
  desk: "oklch(97.4% 0.004 286)"
  paper: "oklch(100% 0 0)"
  paper-ruled: "oklch(97.6% 0.003 286)"
  ink: "oklch(23.5% 0.004 286)"
  ink-soft: "oklch(46% 0.007 286)"
  ink-faint: "oklch(57% 0.007 286)"
  plate: "oklch(24% 0.004 286)"
  lilac: "oklch(91% 0.055 300)"
  lilac-ink: "oklch(36% 0.12 295)"
  stamp-blue: "oklch(49% 0.19 272)"
  stamp-red: "oklch(51% 0.19 27)"
  stamp-ochre: "oklch(52% 0.12 75)"
  canary: "oklch(91% 0.12 88)"
  canary-ink: "oklch(44% 0.11 65)"
  canary-mark: "oklch(78% 0.16 82)"
  violet: "oklch(91.5% 0.06 300)"
  violet-ink: "oklch(44% 0.17 300)"
  violet-mark: "oklch(58% 0.19 300)"
  green: "oklch(91.5% 0.085 152)"
  green-ink: "oklch(40% 0.12 152)"
  green-mark: "oklch(63% 0.15 152)"
  sky: "oklch(91.5% 0.055 245)"
  sky-ink: "oklch(43% 0.15 255)"
  sky-mark: "oklch(60% 0.15 245)"
  red: "oklch(90% 0.07 25)"
  red-ink: "oklch(47% 0.19 27)"
  red-mark: "oklch(58% 0.21 27)"
typography:
  title:
    fontFamily: "Source Serif 4 Variable, ui-serif, Georgia, serif"
    fontSize: "2rem"
    fontWeight: 550
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  reading:
    fontFamily: "Inter Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  body:
    fontFamily: "Inter Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.57
    letterSpacing: "normal"
  field-label:
    fontFamily: "Inter Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 500
    lineHeight: 1.45
    letterSpacing: "0.08em"
  meta:
    fontFamily: "Inter Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.47
    letterSpacing: "normal"
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.47
    letterSpacing: "-0.01em"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  full: "9999px"
spacing:
  field: "12px"
  section: "24px"
  page: "24px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "40px"
  button-outline:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "32px"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "36px"
  outcome-chip-pending:
    backgroundColor: "{colors.canary}"
    textColor: "{colors.canary-ink}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  decision-plate:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.paper}"
    rounded: "{rounded.xl}"
    padding: "20px"
---

# Design System: QuoteFlow

## Overview

**Creative North Star: "El agente redacta, una persona decide"**

QuoteFlow tiene un lenguaje editorial sobrio, el de los productos de IA B2B actuales. Usa tarjetas blancas sobre un fondo gris casi blanco, titulares en serif, texto en Inter, rótulos "// SECCIÓN" en mayúsculas pequeñas y botones de tinta casi negra. El sistema prepara la cotización y la persona la aprueba. La pantalla lo deja claro con una sola placa oscura: la decisión pendiente.

El razonamiento queda a la vista en un solo folio, de arriba abajo: el texto del cliente, el recorrido de doce etapas, la regla que actuó y las líneas cotizadas. El tema claro y el oscuro se diseñan juntos. En oscuro la placa se invierte y queda clara.

**Key Characteristics:**
- Tarjetas blancas con borde fino y una sombra amplia y muy tenue sobre un fondo gris frío.
- Titulares en Source Serif 4. Todo lo demás va en Inter.
- Rótulos de sección con el prefijo "// " y una etiqueta enmarcada sobre el título de página.
- Los colores de estado son cinco tintes (canario, celeste, verde, violeta, rojo), siempre con ícono y texto.
- Lila como único acento: selección de texto, aviso de decisión y fila recién decidida.

## Colors

Estrategia: neutros casi acromáticos, cinco tintes de estado, un acento lila y las tintas del sello.

### Primary
- **Tinta** (ink): texto, botón principal, pestaña activa y la placa de decisión (plate).
- **Azul de foco** (stamp-blue): anillo de foco, cursor y el sello "Aprobado".

### Secondary
- **Rojo de sello** (stamp-red): el sello "Rechazado" y los campos con error.
- **Ocre** (stamp-ochre): el sello "Observado".
- **Lila** (lilac / lilac-ink): selección, ícono del aviso de decisión y fondo de la fila recién decidida.

### Tertiary
- **Tintes de estado**: canario (pendiente de aprobación), celeste (necesita aclaración), verde (borrador listo), violeta (detenida) y rojo (rechazada).
  - Los cinco tonos están separados al menos 60° en el círculo cromático para distinguirse de un vistazo.
  - Cada tinte tiene una tinta (`*-ink`) para el texto encima y una marca (`*-mark`), el tono puro, para puntos y para el lomo de color de cada fila.

### Neutral
- **Fondo** (desk): gris con un matiz frío. **Tarjeta** (paper): blanco puro. **Gris de relleno** (paper-ruled): filas, campos de solo lectura y celdas del recorrido.
- **Tinta suave** (ink-soft) para texto secundario y **tinta tenue** (ink-faint) para marcadores de posición y metadatos.

**The Tint Rule.** Un estado se reconoce por tinte, ícono y palabra a la vez; el color nunca va solo.

**The One Plate Rule.** Cada pantalla tiene como máximo una placa oscura, y es la acción que espera a una persona.

## Typography

- **Titulares:** Source Serif 4 Variable con tamaño óptico, peso 550. Se usa en el título de página, el cliente del folio, la marca y "Tu decisión".
- **Texto:** Inter Variable para todo lo demás. Las cifras van con `tabular-nums` para que montos, SKU y folios alineen en columna.
- **Código:** JetBrains Mono 500, solo para identificadores literales del sistema (nombres de nodos en la auditoría).
- **Sello:** Archivo en ancho condensado (78 %), reservada a la palabra del sello.

### Hierarchy
- **Title** (serif 550, 2rem, −0.02em): nombre del cliente y título de página.
- **Reading** (400, 1rem, 1.6): el texto del cliente, con un máximo de 70ch.
- **Body** (400, 0.875rem): texto general y celdas.
- **Field label** (500, 0.6875rem, mayúsculas, 0.08em): rótulo de campo. Los títulos de sección (`h2`) llevan el prefijo "// ".
- **Eyebrow tag** (450, 0.75rem, mayúsculas, 0.04em, recuadro de 1px): etiqueta sobre el título de página, por ejemplo "// COLA DE APROBACIÓN".
- **Meta** (400, 0.75rem): fechas, códigos de cliente y notas. Nada baja de 0.6875rem.
- **Total** (700, 1.125rem, tabular): la única cifra que sube de tamaño.

**The Serif Is a Headline Rule.** La serif solo aparece en titulares. Tablas, controles y cifras van en Inter.

**The Weight Not Size Rule.** Dentro de tablas, el rango se marca con peso y mayúsculas: una fila pendiente pone al cliente en negrita, no en un tamaño mayor.

## Layout

La columna máxima es de 88rem, con un margen de 16 a 24px.

**Bandeja.** Sigue el patrón de las colas de aprobación (Ramp, HubSpot Quotes):
- Dos pestañas: **Por decidir**, la cola de trabajo, y **Todas**, el archivo. "Por decidir" es la vista por defecto cuando hay pendientes y muestra su conteo en canario.
- En "Todas", un desplegable **Estado** con conteos filtra junto al buscador y se quita con una ×.
- La vista y el estado viven en la URL (`?vista=todas&estado=BLOCKED`).
- Debajo va una tabla densa con un lomo de color por fila.
- No hay tablero de métricas: los conteos están en las pestañas y en el desplegable.

**Detalle.** Es un folio en dos columnas desde 1024px: el contenido a la izquierda y el panel de decisión fijo de 22rem a la derecha. En móvil, el panel va primero, debajo del encabezado, y las tablas se desplazan en horizontal dentro de su borde.

**The Registered Stages Rule.** El recorrido siempre muestra las doce etapas en la misma posición (12 columnas, o 6 × 2 en móvil): la que no se recorrió queda atenuada, nunca se oculta.

## Elevation & Depth

Hay dos niveles:
- **Fondo:** plano.
- **Tarjetas y placa:** borde de tinta al 9 % y la sombra `shadow-card`. Es una sombra de contacto de 1px más una difusa de 44px con un desplazamiento de 18px, al 16 %. En oscuro la sombra es negra y más densa.

No hay más niveles, degradados ni vidrio.

## Shapes

- Controles y botones: 6–8px.
- Placas y avisos: 12px.
- Tarjetas principales (bandeja, folio, formulario): 16px.
- Píldoras: etiquetas de estado, conteos de pestaña y chips de ejemplo.
- El único objeto rotado es el sello (−7° aprobado, 5° rechazado, −3° observado).

## Components

### Buttons
- **Primario:** fondo de tinta, texto blanco, peso 500, 40px de alto y esquina de 8px. Al pasar el puntero baja la opacidad.
- **Secundario:** borde fino de 1px sobre blanco, de 32–36px de alto.
- **Dentro de la placa:** "Aprobar y generar borrador" a lo ancho, invertido sobre la placa. Rechazar y Observar van con borde fino.

### Chips
- **Resultado:** píldora con tinte, tinta, ícono de 14px y texto en negrita. En el encabezado del folio va a tamaño mayor.

### Cards / Containers
- **Folio:** tarjeta blanca de 16px con borde, `shadow-card` y un encabezado que contiene el rótulo "// FOLIO Nº …", el cliente en serif y el resultado.
- **Campos:** grilla con rótulo de campo encima del valor.

### Inputs / Fields
- Blancos, con borde de tinta al 16 % y esquina de 8px. Al enfocar, el borde pasa al azul de foco. Con error, el borde se pone rojo y aparece un mensaje que dice qué escribir.

### Navigation
- **Encabezado:** blanco, de 56px de alto, con filete inferior. Lleva la marca "QuoteFlow" en serif, el enlace a la bandeja subrayado cuando está activo, el selector de tema y el botón "Registrar solicitud" en tinta.
- **Selector de tema:** dos botones (sol y luna) en un grupo enmarcado; el activo va relleno de tinta.
  - Un clic cambia el tema.
  - Mientras no se elige nada, sigue al sistema.
  - Elegir el mismo tema que el sistema vuelve a seguirlo.

### Placa de decisión
- **Contenido:** el rótulo "// HUMANO EN EL CICLO", el título "Tu decisión" en serif, los campos y las acciones.
- **Aspecto:** tinta casi negra en claro, gris muy claro en oscuro, con esquina de 16px y `shadow-card`.

### Rastro de decisiones
- Al decidir, el folio se anota en la sesión.
- **De vuelta en la bandeja:**
  - El folio ya salió de "Por decidir".
  - Un aviso blanco con un ícono lila lo confirma: "Aprobaste el folio Nº …, ahora está en … Te quedan N por decidir."
  - El aviso ofrece "Ver en Todas" y "Abrir folio".
- **En "Todas":**
  - La fila destella en lila, queda con un fondo lila tenue y se desplaza a la vista.
  - Debajo de su resultado se lee "Aprobada por ti · recién".

### Sello
- **Forma:** doble filete del color de su tinta. La palabra va en Archivo condensada, extra negrita y espaciada, y debajo la fecha y quien decidió.
- **Color:** se mezcla con la tarjeta (multiply en claro, screen en oscuro).
- **Animación:** al decidir, cae. Entra grande y desenfocado y se asienta en 420ms. Con movimiento reducido no se anima.

## Do's and Don'ts

### Do:
- **Do** mostrar cada resultado con su tinte, su ícono y su palabra.
- **Do** usar la serif solo en titulares y el "// " solo en rótulos de sección.
- **Do** dejar visibles las doce etapas del recorrido, aunque no se hayan recorrido.
- **Do** reservar la placa oscura para la decisión pendiente.

### Don't:
- **Don't** apilar sombras ni inventar nuevas: solo existe `shadow-card`.
- **Don't** usar degradados, ilustraciones de fondo ni vidrio dentro de la consola.
- **Don't** usar el lila para estados: es acento de selección y de "recién decidido".
- **Don't** poner sellos sin una decisión humana detrás: un resultado automático se muestra con su tinte, no con un sello.
