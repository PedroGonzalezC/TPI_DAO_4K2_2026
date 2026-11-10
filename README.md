# TPI 2026 · Tema 1 · Biblioteca

Sistema de préstamos locales e interbibliotecarios para una red de sedes, organizado bajo una arquitectura en capas con Python 3.10+, FastAPI y SQLite. El archivo `Tema1 - Biblioteca.pdf` es el enunciado original de la cátedra y se conserva intacto.

## Interfaz web

La presentación principal se abre en el navegador. Desde esta carpeta:

```powershell
python -m backend.web
```

Abrir **http://127.0.0.1:8000**. El servidor utiliza la base única `biblioteca.db` (que ya viene precargada con datos iniciales de sedes, socios, libros, ejemplares, préstamos, traslados, reservas y multas). Para reiniciar la base a su estado inicial en cualquier momento:

```powershell
python -m backend.demo
python -m backend.web
```

## Ejecución

Abrir una terminal en esta carpeta y ejecutar:

```powershell
python -m backend --help
python -m backend --db biblioteca.db sede-crear "Centro" "San Martín 100" "351-111" "L-V 9-18"
python -m backend --db biblioteca.db sede-crear "Norte" "Colón 200" "351-222" "L-V 9-17"
python -m backend --db biblioteca.db socio-crear 12345678 "Ana Pérez" "ana@example.com"
python -m backend --db biblioteca.db libro-crear 9780000000001 "Diseño con objetos" "A. Autor" --anio 2026
python -m backend --db biblioteca.db ejemplar-crear EJ-001 1 1
python -m backend --db biblioteca.db disponibilidad
```

Cada comando devuelve JSON. Los IDs se asignan al crear registros y se consultan con `listar`:

```powershell
python -m backend --db biblioteca.db listar sedes
python -m backend --db biblioteca.db listar socios
python -m backend --db biblioteca.db listar libros
python -m backend --db biblioteca.db listar ejemplares
```

### Préstamo local

```powershell
python -m backend --db biblioteca.db prestamo-solicitar 1 1 1 1
python -m backend --db biblioteca.db prestamo-entregar 1
python -m backend --db biblioteca.db prestamo-devolver 1 --condicion BUENO
```

### Préstamo entre sedes

Los números `1 1 1 2` significan socio 1, ejemplar 1, sede de origen 1 y sede de destino 2. Usar un ejemplar disponible; si se ejecutó el ejemplo local, ya habrá sido devuelto.

```powershell
python -m backend --db biblioteca.db prestamo-solicitar 1 1 1 2
python -m backend --db biblioteca.db listar remitos
python -m backend --db biblioteca.db remito-avanzar 1 EMPAQUETADO --detalle "Caja sellada"
python -m backend --db biblioteca.db remito-avanzar 1 DESPACHADO --detalle "Sale de Centro"
python -m backend --db biblioteca.db remito-avanzar 1 RECIBIDO --detalle "Ingresa en Norte"
python -m backend --db biblioteca.db remito-historial 1
python -m backend --db biblioteca.db prestamo-entregar 2
python -m backend --db biblioteca.db prestamo-devolver 2 --condicion BUENO
python -m backend --db biblioteca.db listar remitos
```

Al devolver un préstamo interbibliotecario, se crea un remito de regreso. Se lo avanza con `remito-avanzar` de la misma forma. Al recibirlo en la sede de origen, el ejemplar vuelve a estar disponible (o queda en revisión si se devolvió dañado).

### Reservas y administración

```powershell
python -m backend --db biblioteca.db reserva-crear 1 1 1
python -m backend --db biblioteca.db listar reservas
python -m backend --db biblioteca.db reserva-cancelar 1
python -m backend --db biblioteca.db socio-editar 1 --habilitado 0
python -m backend --db biblioteca.db sede-editar 2 --activa 0
python -m backend --db biblioteca.db libro-editar 1 --titulo "Nuevo título"
python -m backend --db biblioteca.db revision-cerrar 1 --apto 1
```

`revision-cerrar` solo corresponde a ejemplares en estado `EN_REVISION`. Las sedes y socios usan baja o inhabilitación lógica para conservar el historial. Se pueden editar dirección, contacto y horarios de sedes, y nombre y correo de socios.

### Reportes

```powershell
python -m backend --db biblioteca.db reporte activos_transito
python -m backend --db biblioteca.db reporte vencidos_multas
python -m backend --db biblioteca.db reporte mas_solicitados
python -m backend --db biblioteca.db reporte disponibilidad
python -m backend --db biblioteca.db reporte logistica
python -m backend --db biblioteca.db reporte movimientos
```

Los seis reportes usan consultas agregadas o cruces de varias entidades. Sus definiciones y alcances figuran en [DISEÑO.md](DISEÑO.md).

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan bases SQLite temporales independientes. Cubren el circuito local e interbibliotecario, la trazabilidad, la persistencia, las reservas en orden, los duplicados, las sedes dadas de baja, los socios inhabilitados, las fechas, las multas, los reportes y la API de la interfaz web.

## Organización (Arquitectura en capas)

- `frontend/`: **4.1. Presentación (React)** — interfaz web en React modularizada en componentes (`src/components/`), vistas por pantalla (`src/views/`), cliente REST (`src/api.js`), entrada (`app.js`, `src/App.jsx`) y estilos (`styles.css`).
- `backend/controllers/`: **4.2. Controllers** — un archivo por controlador FastAPI (`sede_controller.py`, `socio_controller.py`, `catalogo_controller.py`, `reserva_controller.py`, `prestamo_controller.py`, `remito_controller.py`, `multa_controller.py`, `reporte_controller.py`, `schemas.py`, `dependencias.py`).
- `backend/services/`: **4.3. Services** — un archivo por servicio de negocio (`sede_service.py`, `socio_service.py`, `catalogo_service.py`, `reserva_service.py`, `prestamo_service.py`, `remito_service.py`, `multa_service.py`, `reporte_service.py`, `biblioteca_service.py`).
- `backend/models/`: **4.4. Dominio (Models)** — un archivo por entidad/modelo (`sede.py`, `socio.py`, `material.py`, `ejemplar.py`, `reserva.py`, `prestamo.py`, `remito.py`, `multa.py`, `excepciones.py`).
- `backend/daos/`: **4.5. Persistencia / DAO** — un archivo por clase DAO (`sede_dao.py`, `socio_dao.py`, `material_dao.py`, `ejemplar_dao.py`, `solicitud_dao.py`, `prestamo_dao.py`, `reserva_dao.py`, `remito_dao.py`, `evento_remito_dao.py`, `multa_dao.py`).
- `backend/database/`: **4.6. Base de datos** — esquema SQLite (`esquema.py`) y gestor transaccional (`conexion.py`).
- `backend/__main__.py`: interfaz de consola (`python -m backend`).
- `backend/web.py`: servidor local Uvicorn/FastAPI (`python -m backend.web`).
- `backend/demo.py`: carga inicial de la base de muestra (`python -m backend.demo`).
- `tests/`: pruebas automatizadas del dominio, servicios y controllers FastAPI.
- `DISEÑO.md`: modelo, arquitectura en capas, decisiones, procesos y patrones.
- `DESIGN.md` y `UX-CONTRACT.md`: criterios visuales y de interacción de la interfaz.

La base `biblioteca.db` se crea automáticamente al ejecutar el primer comando. Para comenzar una base nueva, utilizar otra ruta con `--db`.
