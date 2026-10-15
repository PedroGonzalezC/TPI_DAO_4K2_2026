---
version: alpha
name: "Red de Bibliotecas"
description: "Mesa de circulación digital con lenguaje de fichas, trayectos y tinta institucional."
colors:
  primary: "#183D3E"
  primary-hover: "#245455"
  background: "#F4F7F6"
  surface: "#FFFFFF"
  surface-muted: "#EAF0EE"
  ink: "#203637"
  ink-muted: "#627675"
  border: "#D7E2DE"
  accent: "#C58242"
  success: "#23745A"
  warning: "#986225"
  danger: "#A94646"
  focus: "#176DA4"
typography:
  display:
    fontFamily: "Georgia, Cambria, serif"
  body:
    fontFamily: "Segoe UI, Aptos, system-ui, sans-serif"
  utility:
    fontFamily: "Consolas, Cascadia Code, ui-monospace, monospace"
rounded:
  DEFAULT: "0.75rem"
  sm: "0.4rem"
  md: "0.75rem"
  lg: "1.2rem"
spacing:
  page-max: "90rem"
  section-gap: "2rem"
components:
  button: {}
  card: {}
  dialog: {}
  table: {}
  input: {}
---

# Red de Bibliotecas · Sistema visual

## Overview

### Creative North Star

Una mesa de circulación de biblioteca pública: fichas legibles, sellos de estado, registro de movimientos y un trayecto claro del ejemplar. La marca se recuerda por la **línea de recorrido** que conecta sede de origen, tránsito y destino. Es una herramienta de trabajo, no una portada editorial.

### Product context and register

- **Audiencia y trabajo principal:** personal de una red de bibliotecas que registra circulación, reserva y traslado de ejemplares; presentación académica del TPI.
- **Mercado y evidencia:** ejercicio de UTN FRC para una red de bibliotecas públicas. El enunciado y `DISEÑO.md` fijan el dominio; no se infiere una región normativa adicional.
- **Idioma:** español de Argentina en toda la interfaz. Fechas en `es-AR`; almacenamiento ISO según el servicio Python.
- **Escena de uso:** escritorio para operación cotidiana, con consulta posible en tablet o móvil. Densidad moderada: datos suficientes para decidir sin sacrificar lectura.
- **Registro:** producto administrativo.
- **Firma memorable:** una banda de recorrido que muestra el movimiento entre sedes y sus estados.
- **Contención:** formularios, tablas, errores y decisiones delicadas usan componentes familiares y textos directos.
- **Anti-referencias:** panel SaaS de tarjetas con gradientes genéricos; sitio de lectura ornamental que dificulta operar; pantalla de consola disfrazada.
- **Tokens:** este archivo es la fuente normativa. `web/styles.css` implementa las variables CSS con los mismos valores; `UX-CONTRACT.md` fija el comportamiento. No hay generador intermedio.

## Colors

El verde petróleo `primary` expresa la red y su trabajo estable. `background` es un gris verdoso frío; `surface` mantiene lectura limpia. `accent` aparece solo en el trayecto y llamadas de atención de circulación, no en cada botón. `success`, `warning` y `danger` tienen significado semántico acompañado de texto. `focus` mantiene un anillo visible distinto del acento. Se ofrece tema claro único; el contraste forzado deja colores al sistema operativo.

## Typography

`display` se reserva para títulos y el nombre del producto, como una ficha bibliográfica. `body` resuelve controles y datos. `utility` identifica códigos, ISBN, IDs y remitos. No se usan mayúsculas decorativas en párrafos. La interfaz se redacta en español y usa fechas locales con día, mes y año.

## Layout

Barra lateral persistente en escritorio y navegación horizontal desplazable en pantallas estrechas. El contenido no supera `page-max`. Las tablas tienen paginación de 10 registros y desborde horizontal propio en móvil; los formularios y diálogos usan altura natural con límites de la ventana. El encabezado, tablas y controles reservan espacio para carga y avisos para evitar saltos. Separación entre secciones de `section-gap`.

## Elevation & Depth

La jerarquía se construye con capas tonales, bordes y tipografía. Solo el diálogo y los elementos flotantes reciben sombra; las tarjetas normales permanecen planas. La línea del recorrido usa contraste y geometría, no un gradiente llamativo.

## Shapes

Controles y tarjetas usan radios moderados `sm`, `md`, `lg`. Los sellos de estado son cápsulas pequeñas, mientras que la línea de recorrido y los divisores conservan bordes rectos. Los iconos son signos simples de texto acompañados siempre por etiquetas.

## Components

### Foundational visual states

Todo control incluye hover, foco visible, pulsado y deshabilitado. Los formularios muestran errores junto al campo y un resumen persistente cuando falla el servidor. La carga usa un indicador textual en un espacio estable. Los estados vacíos proponen la próxima acción; los resultados nulos de búsqueda permiten limpiar el filtro.

### Buttons and actions

Botón sólido para la acción principal del contexto, contorno para secundarias y botón de texto para navegación. Acciones de baja, cancelación y pérdida usan intención `danger` y confirmación propia. El estado ocupado conserva la anchura del botón y evita doble envío.

### Navigation and data display

Navegación por áreas con título de página, descripción operativa y acción principal. Tablas semánticas con búsqueda, orden, rango visible y paginación; estados como texto y sello. La pantalla de préstamos y la de remitos comparten densidad, filtros y acciones por fila.

### Forms and overlays

Campos con etiquetas persistentes. Los `select` son nativos: se acepta explícitamente que el sistema operativo controle el popup. No se usa selector de fecha porque los eventos toman la fecha del servidor. Diálogo propio con foco contenido, Escape y restauración. Avisos de éxito con región viva; errores recuperables permanecen en el formulario.

### Iconography

No depende de una biblioteca de iconos. Pequeños símbolos geométricos en CSS sirven de apoyo, nunca sustituyen el texto de una acción.

### Motion

Transiciones discretas de 120–180 ms en hover y apertura del diálogo. No hay movimiento ambiental. `prefers-reduced-motion` desactiva animaciones.

### Content and data visualization

Lenguaje: “Solicitar préstamo”, “Registrar devolución”, “Despachar remito”. Los reportes muestran cifras con etiquetas y tablas consultables. Multas en pesos argentinos calculadas desde centavos; nunca se presenta una tasa de recepción como una tasa de entregas sin incidentes.

## Do's and Don'ts

- **Do:** mostrar siempre la sede de pertenencia y la sede actual del ejemplar cuando la diferencia afecte una decisión.
- **Do:** mantener las mismas etiquetas y estados en lista, diálogo y aviso.
- **Don't:** usar decoración de libros o estanterías que compita con los datos de circulación.
- **Don't:** ocultar condiciones de riesgo o errores detrás de un color, icono o aviso fugaz.
