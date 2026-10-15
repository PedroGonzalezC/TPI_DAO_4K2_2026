# Contrato de experiencia · Red de Bibliotecas

## Product context

- Audiencia: personal de la red de bibliotecas y evaluadores del TPI.
- Trabajo: registrar datos maestros, préstamos, reservas, remitos, devoluciones y consultar reportes.
- Mercado: ejercicio académico de UTN FRC; instancia local de una biblioteca pública.
- Idioma: español de Argentina (`es-AR`).
- Zona horaria: reloj local de la máquina del servidor; las fechas de negocio se guardan ISO en SQLite.
- Accesibilidad objetivo: WCAG 2.2 AA.

## Business-context sources

| Alcance | Fuente | Tipo | Revisado |
|---|---|---|---|
| Procesos y validaciones | `Tema1 - Biblioteca.pdf` | Enunciado de la cátedra | 2026-10-06 |
| Ciclo de vida, multa, reservas y estados | `DISEÑO.md`, `biblioteca/servicio.py`, `tests/test_biblioteca.py` | Modelo y contrato implementado | 2026-10-06 |
| Autorización/retención | Sin política en el enunciado; servidor solo en `127.0.0.1`, uso de demostración local | Límite de alcance | 2026-10-06 |

## Visual contract

`DESIGN.md` es la fuente normativa y `web/styles.css` su implementación directa. Tema claro único. Cualquier token nuevo se documenta en ambos archivos. El proyecto no usa un sistema previo de componentes.

## Canonical UI Map

| Capacidad | Dueño canónico | Fuente | Variantes | Verificación |
|---|---|---|---|---|
| Table Selection | No aplica: no hay acciones masivas | — | — | Inspección de tablas |
| Select/Listbox | `<select>` nativo y campos de `app.js` | Este contrato | Nativo | Teclado y popup del navegador |
| Date | No hay entrada de fechas | Servicio Python | Fecha de servidor | Pruebas del dominio |
| Form | `openForm` y `renderField` en `app.js` | Este contrato | Crear/editar | Flujo de formulario |
| Scrollbar | Reglas globales de `web/styles.css` | `DESIGN.md` | Desborde de tabla | Estilos y navegador |
| Toast | `notify` en `app.js` | Este contrato | Éxito/info/error | Región viva |
| CRUD | `api`, `openForm`, `refresh` | Servicio Python | Crear/editar | Flujo completo |

## Component behavior

Los botones mantienen etiqueta, intención y posición al cargar; no admiten doble envío. Los campos tienen etiqueta y error asociado, y el primer error recibe foco. Las tablas muestran carga, vacío, sin resultados, error y rango/página. Los diálogos aíslan el fondo, contienen el foco, cierran con Escape y restauran el foco al disparador. Una acción no disponible muestra explicación textual en lugar de parecer interactiva.

## Dataset navigation

Las tablas se paginan de a 10 filas en el cliente, con búsqueda y orden persistidos en URL. La aplicación es una demostración local para cientos de registros, y una instantánea de la base permite resolver referencias cruzadas sin múltiples consultas por fila. La tabla nunca renderiza una lista sin límite; cambios de filtro reinician la página y una mutación la ajusta. La selección masiva no existe. En móvil la tabla conserva sus columnas con desplazamiento horizontal visible.

## Flow ledger

| Operación | Disparo | Espera | Éxito | Error y recuperación | Foco | Fuente |
|---|---|---|---|---|---|---|
| Crear/editar dato maestro | Botón “Agregar”/“Editar” | En diálogo, botón ocupado | Cierra, recarga lista, aviso | Error dentro del diálogo, valores retenidos | Acción o nuevo registro | `servicio.py` |
| Solicitar préstamo | Formulario | Botón ocupado | Lista de préstamos, aviso con ID | Regla de negocio visible, valores retenidos | Lista | `servicio.py` |
| Entregar/devolver | Botón de fila y confirmación cuando corresponde | Botón ocupado | Lista actualizada, importe/vencimiento visible | Diálogo abierto y reconsulta disponible | Fila o acción | `servicio.py` |
| Avanzar remito | Botón de fila | Botón ocupado | Estado e historial actualizados | Conserva detalle para corregir/reintentar | Fila | `modelo.py`, `servicio.py` |
| Reservar/cancelar | Formulario/botón de fila | Botón ocupado | Lista actualizada, aviso | Conserva formulario o explica regla | Acción | `servicio.py` |
| Buscar/ordenar/paginar | Controles de tabla | Sin bloqueo | URL y tabla actualizadas | Sin resultados con limpiar filtro | Control | Este contrato |
| Baja lógica | Botón “Dar de baja” | Confirmación propia | Estado actualizado | Sin cambio y explicación | Botón disparador | `servicio.py` |

## Navigation and responsive behavior

Cada área tiene `document.title` específico. La navegación se refleja en `?vista=...`; filtros, orden y página también viven en URL. Pantalla desconocida vuelve al inicio y mantiene navegación utilizable. El cambio de área conserva filtros propios durante la sesión mediante parámetros de URL. La barra lateral se transforma en navegación horizontal en móvil. Tablas pueden desplazarse horizontalmente sin cortar acciones; no se truncan IDs ni títulos críticos sin acceso completo.

## Overlays and feedback

Un único diálogo `#dialog` sirve para formularios y confirmaciones. Las bajas de sedes y la inhabilitación de socios piden confirmación porque alteran operaciones posteriores; destrucción/extravío también. Aviso global breve para éxito, error persistente dentro del diálogo. No se usan diálogos nativos del navegador. No hay autoguardado; cerrar descarta lo escrito y el botón “Cancelar” es explícito.

## Async and resilience

Mutaciones pesimistas: se espera confirmación del servidor y luego se recarga la instantánea. No se repiten automáticamente POST ni se afirma que un timeout haya revertido la acción. En fallo de red, el formulario permanece abierto y se ofrece reintentar tras revisar el listado. GET puede reintentarse; las respuestas de carga antiguas no sustituyen una más reciente. No existe autenticación ni edición multiusuario contractual: la interfaz está limitada al servidor local.

## Validation

Los formularios usan `novalidate`, verifican campos requeridos antes de enviar y muestran errores junto al control. El servicio Python sigue siendo autoridad para disponibilidad, estado, duplicados y fechas. El servidor no expone excepciones internas al usuario. No se persisten borradores ni datos personales en `localStorage`.

## Verification

- Pruebas del dominio: `python -m unittest discover -s tests -v`.
- Pruebas HTTP: `python -m unittest discover -s tests -v`.
- Auditoría premium: `python <skill>/scripts/audit_project.py . --mode strict`.
- Navegador: escritorio, móvil, teclado, éxito/error, vacío/búsqueda, remito abierto y estado de diálogo.
