# Diseño y justificación del TPI

## Alcance y fuentes

Se implementaron los ocho procesos obligatorios y todas las validaciones indicadas en `Tema1 - Biblioteca.pdf`. Se siguieron los apuntes de la cátedra sobre arquitectura en capas, clases de dominio, patrones de diseño, pruebas, FastAPI, SQLite y objetos de acceso a datos (DAO).

## Arquitectura en capas

1. **Presentación (`frontend/`):** Frontend web encargado de mostrar la información y permitir la interacción de los usuarios mediante llamadas REST.
2. **Controllers (`backend/controllers/`):** Implementados en archivos separados por recurso (`sede_controller.py`, `socio_controller.py`, `catalogo_controller.py`, `reserva_controller.py`, `prestamo_controller.py`, `remito_controller.py`, `multa_controller.py`, `reporte_controller.py`). Reciben solicitudes HTTP, validan la estructura con esquemas Pydantic (`schemas.py`), identifican al usuario y comprueban su autorización por rol (`dependencias.py`), invocan los servicios correspondientes y traducen excepciones de negocio (`app.py`).
3. **Services (`backend/services/`):** Un archivo por servicio (`sede_service.py`, `socio_service.py`, `catalogo_service.py`, `reserva_service.py`, `prestamo_service.py`, `remito_service.py`, `multa_service.py`, `reporte_service.py`, `biblioteca_service.py`). Validan reglas del dominio, coordinan operaciones multi-DAO dentro de una misma transacción, utilizan entidades y patrones, y mantienen la coherencia entre solicitudes, préstamos, ejemplares, reservas, remitos y multas.
4. **Dominio / Models (`backend/models/`):** Un archivo por entidad (`sede.py`, `socio.py`, `material.py`, `ejemplar.py`, `reserva.py`, `prestamo.py`, `remito.py`, `multa.py`, `excepciones.py`) que encapsula datos, comportamientos propios y patrones (`FabricaPrestamos`, `ObservadorRemito`) sin código SQL ni dependencia de FastAPI.
5. **Persistencia / DAO (`backend/daos/`):** Un archivo por DAO (`sede_dao.py`, `socio_dao.py`, `material_dao.py`, `ejemplar_dao.py`, `solicitud_dao.py`, `prestamo_dao.py`, `reserva_dao.py`, `remito_dao.py`, `evento_remito_dao.py`, `multa_dao.py`), sin lógica de negocio ni decisiones de autorización.
6. **Base de datos (`backend/database/`):** Esquema relacional SQLite (`esquema.py`) y gestor transaccional de conexiones (`conexion.py`).

## Diagrama Entidad-Relación (DER) y Modelo de Datos

```mermaid
erDiagram
    SEDES ||--o{ EJEMPLARES : "pertenece (sede_pertenencia_id)"
    SEDES ||--o{ EJEMPLARES : "se ubica en (sede_actual_id)"
    SEDES ||--o{ RESERVAS : "retiro en (sede_id)"
    SEDES ||--o{ PRESTAMOS : "origen (sede_origen_id)"
    SEDES ||--o{ PRESTAMOS : "destino (sede_destino_id)"
    SEDES ||--o{ REMITOS : "origen (origen_id)"
    SEDES ||--o{ REMITOS : "destino (destino_id)"

    SOCIOS ||--o{ RESERVAS : "realiza (socio_id)"
    SOCIOS ||--o{ PRESTAMOS : "solicita (socio_id)"

    LIBROS ||--o{ EJEMPLARES : "tiene copias (libro_id)"
    LIBROS ||--o{ RESERVAS : "se reserva (libro_id)"

    EJEMPLARES ||--o{ RESERVAS : "asignado a (ejemplar_id)"
    EJEMPLARES ||--o{ PRESTAMOS : "se presta en (ejemplar_id)"
    EJEMPLARES ||--o{ REMITOS : "trasladado en (ejemplar_id)"

    PRESTAMOS ||--o{ REMITOS : "genera (prestamo_id)"
    PRESTAMOS ||--o| MULTAS : "origina por atraso (prestamo_id)"
    SOCIOS ||--o{ MULTAS : "adeuda (socio_id)"
    REMITOS ||--o{ HISTORIAL_REMITOS : "registra evento (remito_id)"

    SEDES {
        INTEGER id PK
        TEXT nombre UK
        TEXT direccion
        TEXT contacto
        TEXT horarios
        INTEGER activa
    }

    SOCIOS {
        INTEGER id PK
        TEXT documento UK
        TEXT nombre
        TEXT email
        INTEGER habilitado
    }

    LIBROS {
        INTEGER id PK
        TEXT isbn UK
        TEXT titulo
        TEXT autor
        INTEGER anio
    }

    EJEMPLARES {
        INTEGER id PK
        TEXT codigo UK
        INTEGER libro_id FK
        INTEGER sede_pertenencia_id FK
        INTEGER sede_actual_id FK
        TEXT estado
    }

    RESERVAS {
        INTEGER id PK
        INTEGER socio_id FK
        INTEGER libro_id FK
        INTEGER sede_id FK
        INTEGER ejemplar_id FK
        TEXT estado
        TEXT creada_en
    }

    PRESTAMOS {
        INTEGER id PK
        INTEGER socio_id FK
        INTEGER ejemplar_id FK
        INTEGER sede_origen_id FK
        INTEGER sede_destino_id FK
        TEXT tipo
        TEXT estado
        TEXT solicitado_en
        TEXT entregado_en
        TEXT vence_en
        TEXT devuelto_en
        TEXT condicion_devolucion
        INTEGER multa_centavos
    }

    REMITOS {
        INTEGER id PK
        INTEGER prestamo_id FK
        INTEGER ejemplar_id FK
        TEXT tipo
        INTEGER origen_id FK
        INTEGER destino_id FK
        TEXT estado
        TEXT creado_en
        TEXT recibido_en
    }

    MULTAS {
        INTEGER id PK
        INTEGER prestamo_id FK
        INTEGER socio_id FK
        INTEGER monto_centavos
        INTEGER dias_atraso
        TEXT estado
        TEXT creada_en
        TEXT pagada_en
    }

    HISTORIAL_REMITOS {
        INTEGER id PK
        INTEGER remito_id FK
        TEXT estado
        TEXT fecha
        TEXT detalle
    }
```

## Diagrama de Clases (Dominio, Patrones, Services y DAOs)

```mermaid
classDiagram
    class Sede {
        +int id
        +str nombre
        +str direccion
        +str contacto
        +str horarios
        +bool activa
        +asegurar_activa() void
        +actualizar(direccion, contacto, horarios, activa) void
    }

    class Socio {
        +int id
        +str documento
        +str nombre
        +str email
        +bool habilitado
        +asegurar_habilitado() void
        +actualizar(nombre, email, habilitado) void
    }

    class Material {
        +int id
        +str isbn
        +str titulo
        +str autor
        +int anio
        +actualizar(titulo, autor, anio) void
    }

    class Ejemplar {
        +int id
        +str codigo
        +int libro_id
        +int sede_pertenencia_id
        +int sede_actual_id
        +str estado
        +esta_disponible bool
        +asegurar_en_sede_origen(sede_origen_id) void
        +apartar() void
        +reservar() void
        +liberar() void
        +prestar() void
        +despachar() void
        +recibir_en(sede_destino_id, estado_final) void
        +cerrar_revision(apto) void
    }

    class Reserva {
        +int id
        +int socio_id
        +int libro_id
        +int sede_id
        +int ejemplar_id
        +str estado
        +str creada_en
        +asegurar_corresponde_a_solicitud(socio_id, sede_destino_id) void
        +asignar(ejemplar_id) void
        +cumplir() void
        +cancelar() int
    }

    class Prestamo {
        <<abstract>>
        +int id
        +int socio_id
        +int ejemplar_id
        +int sede_origen_id
        +int sede_destino_id
        +str estado
        +str solicitado_en
        +str entregado_en
        +str vence_en
        +str devuelto_en
        +str condicion_devolucion
        +int multa_centavos
        +tipo* str
        +requiere_remito bool
        +estado_requerido_entrega str
        +marcar_en_transito() void
        +marcar_listo() void
        +entregar(ahora, fecha_minima_iso, plazo_dias) str
        +devolver(ahora, condicion, multa_diaria_centavos) tuple
        +estado_ejemplar_al_recibir_retorno() str
    }

    class PrestamoLocal {
        +tipo str
    }

    class PrestamoInterbibliotecario {
        +tipo str
    }

    class FabricaPrestamos {
        <<Factory>>
        +crear(socio_id, ejemplar_id, origen, destino, solicitado_en)$ Prestamo
        +reconstruir(...)$ Prestamo
    }

    class ObservadorRemito {
        <<interface>>
        +actualizar(remito_id, estado, fecha, detalle) void
    }

    class Remito {
        +int id
        +str estado
        +int prestamo_id
        +int ejemplar_id
        +str tipo
        +int origen_id
        +int destino_id
        +str creado_en
        +str recibido_en
        +list~ObservadorRemito~ observadores
        +suscribir(observador) void
        +notificar(estado, fecha_iso, detalle) void
        +registrar_creacion(fecha, detalle) void
        +requiere_sedes_activas(nuevo_estado) bool
        +avanzar(nuevo_estado, fecha, detalle, ultima_fecha_iso) void
    }

    class EventoRemito {
        +int id
        +int remito_id
        +str estado
        +str fecha
        +str detalle
    }

    class EventoRemitoDAO {
        +Connection con
        +registrar(evento) int
        +actualizar(remito_id, estado, fecha, detalle) void
        +obtener_ultimo_por_remito(remito_id) EventoRemito
        +listar_por_remito(remito_id) list
    }

    Prestamo <|-- PrestamoLocal
    Prestamo <|-- PrestamoInterbibliotecario
    FabricaPrestamos ..> PrestamoLocal : instancia
    FabricaPrestamos ..> PrestamoInterbibliotecario : instancia
    Remito o--> ObservadorRemito : notifica
    ObservadorRemito <|.. EventoRemitoDAO : implementa
    EventoRemitoDAO ..> EventoRemito : persiste
    Material "1" <-- "*" Ejemplar : cataloga
    Sede "1" <-- "*" Ejemplar : pertenece / ubica
    Socio "1" <-- "*" Reserva : solicita
    Socio "1" <-- "*" Prestamo : titular
    Ejemplar "1" <-- "*" Prestamo : objeto de
    Prestamo "1" <-- "0..2" Remito : traslada
    Prestamo "1" <-- "0..1" Multa : genera por atraso
    Socio "1" <-- "*" Multa : adeuda

    class Multa {
        +int id
        +int prestamo_id
        +int socio_id
        +int monto_centavos
        +int dias_atraso
        +str estado
        +str creada_en
        +str pagada_en
        +bool esta_pendiente
        +pagar(ahora) void
    }

    class MultaDAO {
        +Connection con
        +crear(multa) int
        +obtener_por_id(multa_id) Multa
        +actualizar(multa) void
        +tiene_pendientes_por_socio(socio_id) bool
        +listar() list
    }
```

- **Sede:** nombre único, dirección, contacto, horarios y estado activo/baja.
- **Socio:** documento único, nombre, correo y habilitación.
- **Libro:** ISBN único, título, autor y año. El ISBN identifica una ficha del catálogo, no un ejemplar físico.
- **Ejemplar:** código único, libro, sede de pertenencia, última sede física conocida y estado de disponibilidad.
- **Préstamo:** socio, ejemplar, origen, destino, tipo, estado, fechas, condición de devolución y multa. El tipo surge de comparar las sedes.
- **Remito:** identifica cada traslado de ida o regreso, con origen, destino, estado y fechas. Cada cambio produce un evento de historial.
- **Reserva:** pedido por socio, libro y sede de retiro. Su asignación es por orden de llegada.
- **Multa:** registro persistente originado al devolver un préstamo con atraso. Conserva el monto en centavos, días de atraso y su estado (`PENDIENTE` o `PAGADA`). Mientras esté `PENDIENTE`, el socio permanece inhabilitado para nuevos préstamos o reservas hasta que se registre su pago.

Las claves foráneas, restricciones `UNIQUE`, `CHECK` e índices parciales de SQLite evitan duplicados y más de un préstamo vigente para el mismo ejemplar. Las operaciones que modifican varias tablas se ejecutan en una sola transacción.

## Ciclos de vida

```mermaid
stateDiagram-v2
    [*] --> CREADO
    CREADO --> EMPAQUETADO
    EMPAQUETADO --> DESPACHADO
    DESPACHADO --> RECIBIDO
    RECIBIDO --> [*]
```

El remito registra `CREADO` al generarse y cada transición con fecha y detalle. No se permite saltar ni repetir estados, ni registrar eventos anteriores al estado precedente. Antes de empaquetar o despachar, ambas sedes deben estar activas. La recepción puede completar un envío ya iniciado aunque una sede haya sido dada de baja después del despacho.

Un préstamo local pasa `SOLICITADO → ACTIVO → DEVUELTO`. Uno interbibliotecario pasa `SOLICITADO → EN_TRANSITO → LISTO → ACTIVO → DEVUELTO`. La entrega solo es posible después de la recepción en la sede de destino. Una devolución interbibliotecaria en buen estado o dañada genera un segundo remito de tipo `REGRESO`. El ejemplar no vuelve a estar disponible hasta recibir ese remito en la sede de origen. Una devolución dañada queda en revisión; el personal decide si vuelve a circulación o se da de baja. Un ejemplar destruido o extraviado se da de baja.

Estados del ejemplar: `DISPONIBLE`, `APARTADO`, `RESERVADO`, `PRESTADO`, `EN_TRANSITO`, `POR_RETORNAR`, `EN_REVISION`, `BAJA`. La sede actual representa la última ubicación física confirmada; mientras viaja, el remito indica su trayecto.

## Reglas de negocio y decisiones explícitas

| Regla | Aplicación |
|---|---|
| Ejemplar disponible | Solo se solicita si está `DISPONIBLE` o `RESERVADO` para el mismo socio. |
| Socio habilitado | Se verifica al reservar, solicitar y entregar. |
| Sedes activas | Se verifican al reservar, solicitar y comenzar o despachar remitos. |
| Propiedad del ejemplar | La sede de origen debe ser su sede de pertenencia y su ubicación actual. |
| Duplicados | Documento, ISBN, código de ejemplar y nombre de sede únicos. |
| Vencimiento | Catorce días corridos desde la entrega; no desde la solicitud. |
| Multa | $100 por día corrido de atraso. Al devolver con atraso se crea un registro en `multas` con estado `PENDIENTE` y el socio queda inhabilitado hasta que se registre el pago (`PAGADA`). |
| Reservas | Cola por libro y sede; se asigna el primer ejemplar disponible a la primera reserva vigente de socio habilitado. Solo el titular puede solicitar ese ejemplar. |
| Condición de devolución | `BUENO`, `DANADO`, `DESTRUIDO` o `EXTRAVIADO`. |

El plazo y la multa son decisiones de diseño porque el enunciado pide control de vencimientos y reportes de multas, pero no indica valores. Están centralizados en `Biblioteca.PLAZO_DIAS` y `Biblioteca.MULTA_DIARIA_CENTAVOS` para facilitar su cambio. Las reservas se gestionan en la sede de retiro y se asignan a ejemplares físicamente disponibles en ella. Los materiales interbibliotecarios regresan siempre a su sede de pertenencia.

## Patrones de diseño aplicados

1. **Factory / fábrica simple:** `FabricaPrestamos.crear` encapsula la elección entre `PrestamoLocal` y `PrestamoInterbibliotecario`. El caso de uso solicita un préstamo sin instanciar clases concretas. El tipo se persiste y determina si se necesita remito.
2. **Observer:** `Remito` notifica cada transición a `HistorialRemito`, que guarda el evento en `historial_remitos`. La transición y el evento se confirman en la misma transacción; si falla, ambos se revierten. Este desacoplamiento permite agregar otros observadores (por ejemplo, notificaciones) sin modificar el remito.

## Reportes implementados

| Nombre | Contenido |
|---|---|
| `activos_transito` | Préstamos activos, listos o en tránsito y remitos de regreso despachados, con libro, socio, ejemplar y sedes del trayecto. |
| `vencidos_multas` | Préstamos activos vencidos, días de atraso y multa estimada a la fecha de consulta. |
| `mas_solicitados` | Libros ordenados por solicitudes interbibliotecarias. |
| `disponibilidad` | Total, disponibles y en tránsito por libro y última sede conocida. |
| `logistica` | Remitos totales, recibidos, en tránsito, porcentaje recibido y tiempo medio desde creación a recepción. |
| `movimientos` | Cantidad y tiempo medio de traslados por par origen/destino y tipo ida/regreso. |

La tasa de recepción no es una tasa de entregas sin incidentes: solo expresa qué porcentaje de remitos creados ya llegó. El enunciado propone incidencias como reporte sugerido, pero el registro detallado de incidencias es un proceso opcional no implementado.

## Correspondencia con el enunciado

| Proceso obligatorio | Comandos / métodos |
|---|---|
| Sedes | `sede-crear`, `sede-editar`, `listar sedes` |
| Socios | `socio-crear`, `socio-editar`, `listar socios` |
| Catálogo y ejemplares | `libro-crear`, `libro-editar`, `ejemplar-crear`, `listar` |
| Solicitudes locales e interbibliotecarias | `prestamo-solicitar`, `prestamo-entregar` |
| Empaquetar, despachar y recibir | `remito-avanzar`, `remito-historial` |
| Disponibilidad | `disponibilidad`, reporte homónimo |
| Reservas | `reserva-crear`, `reserva-cancelar`, `listar reservas` |
| Devoluciones y condición física | `prestamo-devolver`, `revision-cerrar` |

Los procesos opcionales de notificaciones, historial de lecturas y recomendaciones no forman parte de esta entrega.
