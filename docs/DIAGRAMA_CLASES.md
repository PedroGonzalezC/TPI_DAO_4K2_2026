# Diagrama de clases de la biblioteca

Este diagrama representa **las clases Python que existen en el código**. Las entidades se reconstruyen desde SQLite mediante sus DAO: una fila persistida no se entrega directamente a la lógica de negocio.

```mermaid
classDiagram
    direction LR

    class ManejadorWeb {
        -biblioteca: Biblioteca
        -nombre_base: str
        +do_GET()
        +do_POST()
    }

    class Biblioteca {
        +db: BaseDatos
        +reportes_dao: ReportesDAO
        +reservar()
        +solicitar_prestamo()
        +avanzar_remito()
        +entregar_prestamo()
        +devolver_prestamo()
        +reportes()
    }

    class CatalogoDAO {
        +obtener()
        +listar()
        +crear_sede()
        +crear_socio()
        +crear_libro()
        +crear_ejemplar()
        +disponibilidad()
    }
    class EjemplarDAO
    class ReservaDAO
    class PrestamoDAO
    class RemitoDAO
    class ReportesDAO {
        +consultar()
    }
    class BaseDatos {
        +ruta: str
        +conexion()
    }
    class HistorialRemito {
        +conexion: sqlite3.Connection
        +actualizar()
    }

    class Prestamo {
        +socio_id: int
        +ejemplar_id: int
        +sede_origen_id: int
        +sede_destino_id: int
        +estado: str
        +tipo: str
        -_estado: EstadoPrestamo
        +avanzar()
    }
    class PrestamoLocal {
        +tipo: str
    }
    class PrestamoInterbibliotecario {
        +tipo: str
    }
    class FabricaPrestamos {
        +crear() Prestamo
    }
    class EstadoPrestamo {
        <<abstract>>
        +nombre: str
        +avanzar()
    }
    class Solicitado
    class EnTransito
    class Listo
    class Activo
    class Devuelto
    class Cancelado

    class Libro
    class Ejemplar {
        +estado: str
        +avanzar()
        +ubicar_en()
    }
    class EstadoEjemplar {
        <<abstract>>
        +nombre: str
        +avanzar()
    }
    class Disponible
    class Reservado
    class ApartadoEjemplar
    class EnTransitoEjemplar
    class PrestadoEjemplar
    class PorRetornar
    class EnRevision
    class Baja
    class Socio {
        +exigir_habilitado()
    }
    class Sede {
        +exigir_activa()
    }
    class Reserva {
        +estado: str
        +asignar_ejemplar()
        +avanzar()
    }
    class EstadoReserva {
        <<abstract>>
        +nombre: str
        +avanzar()
    }
    class EnEspera
    class Asignada
    class Cumplida
    class CanceladaReserva

    class Remito {
        +id: int
        +estado: str
        -_estado: EstadoRemito
        +suscribir()
        +avanzar()
    }
    class EstadoRemito {
        <<abstract>>
        +nombre: str
        +avanzar()
    }
    class Creado
    class Empaquetado
    class Despachado
    class Recibido
    class ObservadorRemito {
        <<Protocol>>
        +actualizar()
    }
    class ReglaNegocio {
        <<exception>>
    }

    ManejadorWeb --> Biblioteca : llama casos de uso
    Biblioteca *-- BaseDatos : abre transacciones
    Biblioteca *-- ReportesDAO : conserva instancia
    Biblioteca ..> CatalogoDAO : listados y disponibilidad
    Biblioteca ..> EjemplarDAO : reconstruye y guarda
    Biblioteca ..> ReservaDAO : reconstruye y guarda
    Biblioteca ..> PrestamoDAO : reconstruye y guarda
    Biblioteca ..> RemitoDAO : reconstruye y guarda
    Biblioteca ..> FabricaPrestamos : crea préstamo
    Biblioteca ..> Remito : avanza
    Biblioteca ..> HistorialRemito : suscribe
    CatalogoDAO ..> ReglaNegocio : valida listado
    ReportesDAO --> BaseDatos : consulta
    ReportesDAO ..> ReglaNegocio : reporte inválido
    FabricaPrestamos ..> PrestamoLocal : instancia
    FabricaPrestamos ..> PrestamoInterbibliotecario : instancia
    Prestamo <|-- PrestamoLocal
    Prestamo <|-- PrestamoInterbibliotecario
    Prestamo *-- EstadoPrestamo : estado vigente
    EstadoPrestamo <|-- Solicitado
    EstadoPrestamo <|-- EnTransito
    EstadoPrestamo <|-- Listo
    EstadoPrestamo <|-- Activo
    EstadoPrestamo <|-- Devuelto
    EstadoPrestamo <|-- Cancelado
    Solicitado ..> EnTransito : interbibliotecario
    Solicitado ..> Activo : local
    EnTransito ..> Listo : siguiente
    Listo ..> Activo : siguiente
    Activo ..> Devuelto : siguiente
    Ejemplar *-- EstadoEjemplar : estado vigente
    EstadoEjemplar <|-- Disponible
    EstadoEjemplar <|-- Reservado
    EstadoEjemplar <|-- ApartadoEjemplar
    EstadoEjemplar <|-- EnTransitoEjemplar
    EstadoEjemplar <|-- PrestadoEjemplar
    EstadoEjemplar <|-- PorRetornar
    EstadoEjemplar <|-- EnRevision
    EstadoEjemplar <|-- Baja
    Reserva *-- EstadoReserva : estado vigente
    EstadoReserva <|-- EnEspera
    EstadoReserva <|-- Asignada
    EstadoReserva <|-- Cumplida
    EstadoReserva <|-- CanceladaReserva
    Remito *-- EstadoRemito : estado vigente
    Remito o-- ObservadorRemito : notifica
    ObservadorRemito <|.. HistorialRemito
    EstadoRemito <|-- Creado
    EstadoRemito <|-- Empaquetado
    EstadoRemito <|-- Despachado
    EstadoRemito <|-- Recibido
    Creado ..> Empaquetado : siguiente
    Empaquetado ..> Despachado : siguiente
    Despachado ..> Recibido : siguiente
```

## Cómo leer el circuito principal

1. La consola (`biblioteca/__main__.py`) o `ManejadorWeb` pide una operación a `Biblioteca`.
2. `Biblioteca` abre una conexión mediante `BaseDatos`, verifica las reglas y llama al DAO correspondiente con **esa misma conexión**.
3. Al solicitar un préstamo, `FabricaPrestamos` crea `PrestamoLocal` o `PrestamoInterbibliotecario`. Ambos reconstruyen su `EstadoPrestamo` desde SQLite; `Ejemplar` avanza a `APARTADO` y el segundo genera un remito de ida.
4. Al avanzar un remito, `Remito` delega la transición a su `EstadoRemito` actual. Solo se admite `Creado → Empaquetado → Despachado → Recibido`; esos cambios hacen avanzar también el préstamo interbibliotecario de `SOLICITADO → EN_TRANSITO → LISTO`.
5. Al entregar o devolver, `Prestamo` delega en su `EstadoPrestamo`: un préstamo local sigue `SOLICITADO → ACTIVO → DEVUELTO`, y uno interbibliotecario sigue `SOLICITADO → EN_TRANSITO → LISTO → ACTIVO → DEVUELTO`. `Ejemplar` y `Reserva` también delegan en State sus cambios de ciclo de vida.
6. `Remito` notifica a `HistorialRemito`, que guarda el evento dentro de la misma transacción. Si falla cualquier paso, `BaseDatos` revierte la operación.

## Ubicación de las clases

| Capa | Archivos que contienen una clase cada uno |
|---|---|
| Dominio | `catalogo/` (`Libro`, `Ejemplar`, `estados_ejemplar/`), `personas/` (`Socio`, `Sede`), `reservas/` (`Reserva`, `estados_reserva/`), `prestamos/` y `remitos/` con sus carpetas de estados; `regla_negocio.py` |
| Aplicación | `aplicacion/biblioteca.py` (fachada y coordinación), `servicio_catalogo.py`, `servicio_personas.py` |
| Persistencia | Un DAO por agregado (`sede_dao.py`, `socio_dao.py`, `libro_dao.py`, `ejemplar_dao.py`, `reserva_dao.py`, `prestamo_dao.py`, `remito_dao.py`), más reportes, historial y transacciones |
| Presentación | `presentacion/manejador_web.py` |

Las rutas de la tabla son relativas al paquete `biblioteca/`. `config.py`, `persistencia/esquema.py`, `presentacion/web_actions.py`, `web.py`, `demo.py` y `__main__.py` contienen constantes o funciones, sin clases adicionales.

Al sumar o cambiar una clase, actualizar este diagrama y la tabla de archivos en el mismo cambio. Así las relaciones dibujadas siguen correspondiendo a los imports y llamadas reales.
