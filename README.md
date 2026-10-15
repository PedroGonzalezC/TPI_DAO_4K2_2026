# TPI 2026 · Tema 1 · Biblioteca

Sistema de préstamos locales e interbibliotecarios para una red de sedes. Implementado en Python 3.10+ y SQLite (`sqlite3` de la biblioteca estándar), sin paquetes externos. El archivo `Tema1 - Biblioteca.pdf` es el enunciado original de la cátedra y se conserva intacto.

No hay instalación de dependencias: alcanza con Python 3.10 o superior. Los comandos se ejecutan desde la raíz del repositorio; `--db` admite una ruta explícita para usar otra base.

## Interfaz web

La presentación principal se abre en el navegador. Desde esta carpeta:

```powershell
python -m biblioteca.web --db biblioteca.db
```

Abrir **http://127.0.0.1:8000**. El servidor solo escucha en la computadora local. La interfaz permite operar sedes, socios, catálogo, ejemplares, préstamos, remitos, reservas y reportes sobre la misma base SQLite que la consola. Para detenerla, presionar `Ctrl+C` en la terminal.

Para una presentación con datos de muestra, crear una **base separada** y abrirla con el mismo servidor:

```powershell
python -m biblioteca.demo --db demo_biblioteca.db
python -m biblioteca.web --db demo_biblioteca.db
```

El generador de muestra se niega a modificar una base existente. La base `biblioteca.db` permanece intacta. La interfaz está pensada como demostración local; no incorpora cuentas ni acceso remoto.

## Ejecución

Abrir una terminal en esta carpeta y ejecutar:

```powershell
python -m biblioteca --help
python -m biblioteca --db biblioteca.db sede-crear "Centro" "San Martín 100" "351-111" "L-V 9-18"
python -m biblioteca --db biblioteca.db sede-crear "Norte" "Colón 200" "351-222" "L-V 9-17"
python -m biblioteca --db biblioteca.db socio-crear 12345678 "Ana Pérez" "ana@example.com"
python -m biblioteca --db biblioteca.db libro-crear 9780000000001 "Diseño con objetos" "A. Autor" --anio 2026
python -m biblioteca --db biblioteca.db ejemplar-crear EJ-001 1 1
python -m biblioteca --db biblioteca.db disponibilidad
```

Cada comando devuelve JSON. Los IDs se asignan al crear registros y se consultan con `listar`:

```powershell
python -m biblioteca --db biblioteca.db listar sedes
python -m biblioteca --db biblioteca.db listar socios
python -m biblioteca --db biblioteca.db listar libros
python -m biblioteca --db biblioteca.db listar ejemplares
```

### Préstamo local

```powershell
python -m biblioteca --db biblioteca.db prestamo-solicitar 1 1 1 1
python -m biblioteca --db biblioteca.db prestamo-entregar 1
python -m biblioteca --db biblioteca.db prestamo-devolver 1 --condicion BUENO
```

### Préstamo entre sedes

Los números `1 1 1 2` significan socio 1, ejemplar 1, sede de origen 1 y sede de destino 2. Usar un ejemplar disponible; si se ejecutó el ejemplo local, ya habrá sido devuelto.

```powershell
python -m biblioteca --db biblioteca.db prestamo-solicitar 1 1 1 2
python -m biblioteca --db biblioteca.db listar remitos
python -m biblioteca --db biblioteca.db remito-avanzar 1 EMPAQUETADO --detalle "Caja sellada"
python -m biblioteca --db biblioteca.db remito-avanzar 1 DESPACHADO --detalle "Sale de Centro"
python -m biblioteca --db biblioteca.db remito-avanzar 1 RECIBIDO --detalle "Ingresa en Norte"
python -m biblioteca --db biblioteca.db remito-historial 1
python -m biblioteca --db biblioteca.db prestamo-entregar 2
python -m biblioteca --db biblioteca.db prestamo-devolver 2 --condicion BUENO
python -m biblioteca --db biblioteca.db listar remitos
```

Al devolver un préstamo interbibliotecario, se crea un remito de regreso. Se lo avanza con `remito-avanzar` de la misma forma. Al recibirlo en la sede de origen, el ejemplar vuelve a estar disponible (o queda en revisión si se devolvió dañado).

### Reservas y administración

```powershell
python -m biblioteca --db biblioteca.db reserva-crear 1 1 1
python -m biblioteca --db biblioteca.db listar reservas
python -m biblioteca --db biblioteca.db reserva-cancelar 1
python -m biblioteca --db biblioteca.db socio-editar 1 --habilitado 0
python -m biblioteca --db biblioteca.db sede-editar 2 --activa 0
python -m biblioteca --db biblioteca.db libro-editar 1 --titulo "Nuevo título"
python -m biblioteca --db biblioteca.db revision-cerrar 1 --apto 1
```

`revision-cerrar` solo corresponde a ejemplares en estado `EN_REVISION`. Las sedes y socios usan baja o inhabilitación lógica para conservar el historial. Se pueden editar dirección, contacto y horarios de sedes, y nombre y correo de socios.

### Reportes

```powershell
python -m biblioteca --db biblioteca.db reporte activos_transito
python -m biblioteca --db biblioteca.db reporte vencidos_multas
python -m biblioteca --db biblioteca.db reporte mas_solicitados
python -m biblioteca --db biblioteca.db reporte disponibilidad
python -m biblioteca --db biblioteca.db reporte logistica
python -m biblioteca --db biblioteca.db reporte movimientos
```

Los seis reportes usan consultas agregadas o cruces de varias entidades. Sus definiciones y alcances figuran en [DISEÑO.md](DISEÑO.md).

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan bases SQLite temporales independientes. Cubren el circuito local e interbibliotecario, la trazabilidad, la persistencia, las reservas en orden, los duplicados, las sedes dadas de baja, los socios inhabilitados, las fechas, las multas, los reportes y la API de la interfaz web.

## Organización

- `biblioteca/`: dominio, casos de uso, persistencia y presentación; los archivos se detallan en «Arquitectura y responsabilidades».
- `web/`: interfaz adaptable para navegador.
- `tests/`: pruebas automatizadas del sistema y la API.
- `DISEÑO.md`: modelo, decisiones, procesos, patrones y matriz de validación.
- `docs/DIAGRAMA_CLASES.md`: clases, relaciones y recorrido de una operación.
- `DESIGN.md` y `UX-CONTRACT.md`: criterios visuales y de interacción de la interfaz.

La base `biblioteca.db` se crea automáticamente en la **raíz del repositorio** al ejecutar el primer comando, aunque se invoque el módulo desde otro directorio. `BaseDatos` crea las tablas faltantes con `CREATE TABLE IF NOT EXISTS` y no borra los registros existentes. Para comenzar una base nueva, utilizar otra ruta con `--db`. Las rutas explícitas relativas se interpretan respecto del directorio de la terminal. Las pruebas usan bases temporales; `demo_biblioteca.db` es independiente y el generador se niega a sobrescribir una base con datos.

## Arquitectura y responsabilidades

```text
biblioteca/
  dominio/              préstamos, remito, estados, observador y reglas
  aplicacion/           Biblioteca: casos de uso y validaciones
  persistencia/         BaseDatos, esquema, DAO e historial
  presentacion/         manejador HTTP y traducción de acciones
  config.py             rutas por defecto
  __main__.py           entrada de consola
  web.py                entrada del servidor local
  demo.py               datos de muestra en una base separada
web/                   interfaz HTML, CSS y JavaScript
tests/                 pruebas del dominio y la API
docs/DIAGRAMA_CLASES.md diagrama de clases de la implementación
```

Cada clase propia está en un archivo que lleva su nombre. El [diagrama de clases](docs/DIAGRAMA_CLASES.md) muestra las clases, sus archivos y el recorrido principal. `Biblioteca` recibe una ruta de base y abre una transacción por operación. Los DAO reciben la misma conexión para que cambios en préstamo, ejemplar, remito e historial se confirmen o reviertan juntos. Las clases de `dominio/` no importan `sqlite3` ni conocen la interfaz. Consola y web llaman a los mismos casos de uso.

## Patrones en uso

| Patrón | Participantes | Uso y extensión |
|---|---|---|
| Fábrica simple | `FabricaPrestamos`, `PrestamoLocal`, `PrestamoInterbibliotecario` | `solicitar_prestamo` crea el tipo según las sedes; un tipo nuevo requeriría ampliar esa decisión. Es una fábrica simple, no una implementación completa de Factory Method. |
| Observer | `Remito`, `ObservadorRemito`, `HistorialRemito` | Cada avance del remito registra un evento dentro de la transacción. Se puede suscribir otro observador para un efecto adicional. |
| State | `Remito`, `EstadoRemito`, `Creado`, `Empaquetado`, `Despachado`, `Recibido` | `Remito.avanzar` delega en el estado vigente la transición válida. Cada operación reconstruye el estado desde SQLite y rechaza saltos o avances tras `RECIBIDO`. |
| DAO | `CatalogoDAO`, `CirculacionDAO`, `ReportesDAO` | El servicio decide reglas y coordina; los DAO encapsulan consultas parametrizadas. |

No se agregó Singleton: una conexión corta por operación facilita transacciones independientes y pruebas aisladas. Tampoco se agregó Builder: los objetos actuales se construyen con pocos datos obligatorios. El plazo y la multa fija son reglas únicas del sistema, por lo que Strategy no aportaría una variación real; el recorrido de listas usa el iterador propio de Python.

## Relación con el material de la cátedra

| Concepto verificado | Referencia | Implementación y motivo |
|---|---|---|
| Procesos, validaciones, patrones y reportes mínimos | `Tema1 - Biblioteca.pdf`, pp. 1–2 | Casos de uso en `Biblioteca`, tres patrones y seis reportes. |
| Clases, encapsulamiento y composición | `semana4.pdf`, capítulos 7–9; `semana-05.pdf`, capítulo 10 | `Remito` compone un estado y observadores; los dos tipos de préstamo comparten una base. |
| SQLite, transacciones y DAO | `semana-08.pdf`, pp. 1–16, en especial pp. 8 y 13–16; `Material conceptual.pdf`, pp. 1–10 | `BaseDatos.conexion` usa `commit`/`rollback`; los DAO concentran SQL parametrizado. Se usa `sqlite3`, aunque `semana-08.pdf` también presenta ORM más adelante. |
| Fábrica y Observer | `Patrones.pdf`, pp. 9–16 | Creación del tipo de préstamo y registro desacoplado del historial del remito. |
| State | `Semana 10. Patrones_Strategy_State_Iterator.pdf`, pp. 11–12; `semana-09.pdf`, pp. 17–25 | El estado vigente decide el siguiente avance del remito. |
| Singleton y sus límites | `Patrones.pdf`, pp. 6–8; `semana-09.pdf`, pp. 1–16 | Evaluado para la conexión; se eligió una conexión por operación por las transacciones y el aislamiento en pruebas. |

`semana1.pdf` (programación estructurada), `semana2.pdf` (programación funcional) y `semana3.pdf` (persistencia en archivos) sirven de base conceptual, pero no imponen patrones adicionales al TPI. En el material provisto no se identificó una consigna que obligue a Builder o Strategy. Los ejemplos docentes se adaptaron al dominio de remitos y préstamos, sin copiarlos literalmente.

## Demostración para la defensa

1. Crear `demo_biblioteca.db` y abrir la web con los dos comandos de la sección «Interfaz web».
2. Mostrar sedes, socios, catálogo y disponibilidad inicial.
3. Solicitar un préstamo interbibliotecario con un ejemplar disponible; mostrar el remito `CREADO`.
4. Avanzarlo por `EMPAQUETADO`, `DESPACHADO` y `RECIBIDO`, consultando el historial. Intentar saltar un estado para mostrar la validación State.
5. Entregar, devolver y recibir el remito de regreso; comprobar disponibilidad y ejecutar los reportes.
6. Detener y reiniciar el servidor con la misma base para mostrar que los registros permanecen.
