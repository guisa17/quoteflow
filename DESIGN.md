---
name: QuoteFlow
description: Consola de cotización B2B con forma de talonario autocopiativo; cada decisión humana es un sello.
colors:
  desk: "oklch(94.6% 0.006 85)"
  paper: "oklch(98.9% 0.003 85)"
  paper-ruled: "oklch(96.4% 0.005 85)"
  ink: "oklch(24% 0.045 262)"
  ink-soft: "oklch(45% 0.03 262)"
  ink-faint: "oklch(62% 0.02 262)"
  bar: "oklch(26% 0.075 263)"
  stamp-blue: "oklch(47% 0.17 263)"
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
    fontFamily: "Archivo Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.625rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  reading:
    fontFamily: "Archivo Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  body:
    fontFamily: "Archivo Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.57
    letterSpacing: "normal"
  field-label:
    fontFamily: "Archivo Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.33
    letterSpacing: "0.055em"
  meta:
    fontFamily: "Archivo Variable, ui-sans-serif, system-ui, sans-serif"
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
  xl: "14px"
  full: "9999px"
spacing:
  field: "12px"
  section: "24px"
  page: "24px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.sm}"
    padding: "0 16px"
    height: "36px"
  button-outline:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "32px"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0 12px"
    height: "36px"
  outcome-chip-pending:
    backgroundColor: "{colors.canary}"
    textColor: "{colors.canary-ink}"
    rounded: "{rounded.full}"
    padding: "2px 6px"
  decision-plate:
    backgroundColor: "{colors.bar}"
    textColor: "{colors.paper}"
    rounded: "{rounded.lg}"
    padding: "16px"
---

# Design System: QuoteFlow

## Overview

**Creative North Star: "El talonario y el sello"**

QuoteFlow se ve como el talonario de cotización numerado que usa una oficina comercial: papel con campos reglados, copias de colores y un sello de goma cuando alguien decide. El mundo solo aporta tipografía, paleta, densidad y un gesto propio; la navegación, las tablas y los controles son los estándar de una aplicación web.

El razonamiento queda a la vista: el texto del cliente, el recorrido de doce etapas, la regla que actuó y las líneas cotizadas se leen de arriba abajo en un solo folio. La pantalla funciona igual en claro (papel bajo luz de oficina) y en oscuro (papel carbón).

**Key Characteristics:**
- Folios sobre un escritorio: una hoja de papel con borde fino sobre un fondo apenas más oscuro, sin sombras.
- Los colores de estado son tintes de copia: canario, celeste, verde, violeta y rojo, siempre con ícono y texto.
- Una sola placa invertida por pantalla: la decisión pendiente.
- La decisión humana queda como un sello con palabra, fecha y nombre.

## Colors

Estrategia: neutros de papel y tinta, más cinco tintes de copia que hacen el trabajo de estado, y dos tintas de sello.

### Primary
- **Tinta de talonario** (bar, ink): la barra superior, la placa de decisión, el texto y el botón principal.
- **Tinta de sello azul** (stamp-blue): el sello "Aprobado", el foco y el cursor de escritura.

### Secondary
- **Tinta de sello roja** (stamp-red): el sello "Rechazado" y los campos con error.
- **Tinta ocre** (stamp-ochre): el sello "Observado".

### Tertiary
- **Tintes de copia**: canario (pendiente de aprobación), celeste (necesita aclaración), verde (borrador listo), violeta (detenida), rojo (rechazada). Los cinco tonos están separados al menos 60° en el círculo cromático para distinguirse de un vistazo. Cada tinte tiene su tinta (`*-ink`) para el texto encima y su marca (`*-mark`), el tono puro, para puntos y para el lomo de color de cada fila de la bandeja.

### Neutral
- **Escritorio** (desk) de fondo, **papel** (paper) para los folios y **papel reglado** (paper-ruled) para filas, campos de solo lectura y celdas del recorrido.
- **Tinta suave** (ink-soft) para texto secundario y **tinta tenue** (ink-faint) para marcadores de posición y metadatos.

**The Copy Tint Rule.** Un estado se reconoce por tinte, ícono y palabra a la vez; el color nunca va solo.

**The One Plate Rule.** Cada pantalla tiene como máximo una placa invertida, y es la acción que espera a una persona.

## Typography

**Una sola familia:** Archivo Variable en ancho normal para todo, incluidas las cifras, con `tabular-nums` para que montos, SKU y folios alineen en columna.
**Código:** JetBrains Mono 500 solo para identificadores literales del sistema (nombres de nodos en la auditoría).
**Ancho condensado:** reservado a la palabra del sello (78 %).

### Hierarchy
- **Title** (600, 1.625rem, −0.02em): nombre del cliente y título de página.
- **Reading** (400, 1rem, 1.6): el texto del cliente, con un máximo de 70ch.
- **Body** (400, 0.875rem): texto general y celdas.
- **Field label** (600, 0.75rem, mayúsculas, 0.055em): rótulo de cada sección o campo, como en un formulario impreso.
- **Meta** (400, 0.75rem): fechas, códigos de cliente y notas. Nada baja de 0.6875rem.
- **Total** (700, 1.125rem, tabular): la única cifra que sube de tamaño.

**The One Voice Rule.** Montos, códigos y texto comparten la misma Archivo; la monoespaciada no es un disfraz técnico, solo marca código literal.

**The Weight Not Size Rule.** Dentro de tablas, el rango se marca con peso y mayúsculas: una fila pendiente pone al cliente en negrita, no en un tamaño mayor.

## Layout

Columna máxima de 88rem con margen de 16–24px. La bandeja es una franja de conteos que filtra y una tabla densa de filas de 40px. El detalle es un folio en dos columnas desde 1024px: contenido a la izquierda y panel de decisión fijo de 22rem a la derecha. En móvil, el panel va primero, debajo del encabezado, y las tablas se desplazan en horizontal dentro de su borde.

**The Registered Stages Rule.** El recorrido siempre muestra las doce etapas en la misma posición (12 columnas, o 6 × 2 en móvil): la que no se recorrió queda atenuada, nunca se oculta.

## Elevation & Depth

Plano por completo. La profundidad viene de capas de papel (escritorio → folio → papel reglado) y de bordes finos de tinta al 13 % y 26 %. No hay sombras.

## Shapes

Esquinas de cartulina: suaves sin llegar a burbuja. 6–8px en campos y botones, 12px en placas y 14px en folios. Las etiquetas de estado, los chips de ejemplo, el botón de registrar y el selector de tema son píldoras. El único objeto rotado es el sello (−7° aprobado, 5° rechazado, −3° observado).

## Components

### Buttons
- **Primario:** fondo de tinta, texto de papel, negrita y 36px de alto. Al pasar el puntero baja la opacidad.
- **Dentro de la placa:** "Aprobar y generar borrador" a lo ancho, invertido sobre la placa; Rechazar y Observar con borde fino.

### Chips
- **Resultado:** tinte de copia, tinta, ícono de 14px y texto en negrita; en el encabezado del folio va a tamaño mayor.

### Cards / Containers
- **Folio:** papel con borde fino y esquina de 6px; encabezado con número de folio en mono, cliente y resultado.
- **Campos:** grilla reglada con rótulo de campo encima del valor.

### Inputs / Fields
- Papel, borde de tinta al 26 %, esquina de 3px; al enfocar, el borde pasa a tinta azul de sello. Con error, borde rojo y un mensaje que dice qué escribir.

### Navigation
- Barra de tinta de 48px con la marca "QF" (doble filete), el enlace a la bandeja subrayado cuando está activo, el selector de tema y el botón de registrar en papel.
- **Selector de tema:** dos botones (sol y luna) en una píldora; el activo va relleno. Un clic cambia el tema. Mientras no se elige nada sigue al sistema, y elegir el mismo tema que el sistema vuelve a seguirlo.

### Rastro de decisiones
- Al decidir, el folio se anota en la sesión. De vuelta en la bandeja aparece un aviso ("Aprobaste el folio Nº …, ahora está en …"), la fila destella en azul de sello, queda con un fondo tenue y se desplaza a la vista. Debajo de su resultado se lee "Aprobada por ti · recién". Las demás filas decididas en la sesión conservan la línea "… por ti".

### Sello
- Doble filete del color de su tinta, la palabra en mayúsculas extra negritas y espaciadas, y debajo la fecha y quien decidió. Se mezcla con el papel (multiply en claro, screen en oscuro). Al decidir, cae: entra grande y desenfocado y se asienta en 420ms con curva exponencial; sin animación si se pide movimiento reducido.

## Do's and Don'ts

### Do:
- **Do** mostrar cada resultado con su tinte, su ícono y su palabra.
- **Do** dejar visibles las doce etapas del recorrido, aunque no se hayan recorrido.
- **Do** escribir cifras, SKU y folios en la mono tabular.
- **Do** reservar la placa invertida para la decisión pendiente.

### Don't:
- **Don't** usar sombras, degradados ni vidrio: la profundidad es papel sobre papel.
- **Don't** convertir el talonario en disfraz: nada de texturas de papel, renglones falsos ni tipografía de máquina de escribir en los controles.
- **Don't** poner sellos sin una decisión humana detrás: un resultado automático se muestra con su tinte, no con un sello.
