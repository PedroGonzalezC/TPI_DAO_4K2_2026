# TPI 2026 · Tema 1 · Biblioteca

Sistema de préstamos locales e interbibliotecarios para una red de sedes. Implementado en Python 3.10+ y SQLite, sin paquetes externos. El archivo `Tema1 - Biblioteca.pdf` es el enunciado original de la cátedra y se conserva intacto.

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

- `biblioteca/modelo.py`: entidades del préstamo, fábrica y observador del remito.
- `biblioteca/datos.py`: esquema SQLite, conexiones, transacciones e historial.
- `biblioteca/servicio.py`: casos de uso y reglas de negocio.
- `biblioteca/__main__.py`: interfaz de consola.
- `biblioteca/web.py`: servidor local y API de la interfaz web.
- `biblioteca/demo.py`: carga inicial de la base de muestra.
- `web/`: interfaz adaptable para navegador.
- `tests/`: pruebas automatizadas del sistema y la API.
- `DISEÑO.md`: modelo, decisiones, procesos, patrones y matriz de validación.
- `DESIGN.md` y `UX-CONTRACT.md`: criterios visuales y de interacción de la interfaz.

La base `biblioteca.db` se crea automáticamente al ejecutar el primer comando. Para comenzar una base nueva, utilizar otra ruta con `--db`.
