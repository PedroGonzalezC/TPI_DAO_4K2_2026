# TPI 2026 · Tema 1 · Biblioteca

Sistema de préstamos locales e interbibliotecarios para una red de sedes. Implementado en Python 3.10+, FastAPI y SQLite. El archivo `Tema1 - Biblioteca.pdf` es el enunciado original de la cátedra y se conserva intacto.

## Interfaz web

Ejecutá los siguientes comandos desde la carpeta raíz del proyecto. La primera vez, creá el entorno e instalá las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Creá una cuenta de personal para la base elegida. El programa pedirá la contraseña sin mostrarla en pantalla:

```powershell
.\.venv\Scripts\python.exe -m backend.services.usuarios --db biblioteca.db --usuario personal
.\.venv\Scripts\python.exe -m backend.web --db biblioteca.db
```

Abrí **http://127.0.0.1:8000** e ingresá con la cuenta creada. El servidor solo escucha en la computadora local. Para detenerlo, presioná `Ctrl+C` en la terminal. La documentación de endpoints está en `/docs`.

Para una presentación con datos de muestra, crear una **base separada** y abrirla con el mismo servidor:

```powershell
.\.venv\Scripts\python.exe -m backend.demo --db demo_biblioteca.db
.\.venv\Scripts\python.exe -m backend.services.usuarios --db demo_biblioteca.db --usuario personal
.\.venv\Scripts\python.exe -m backend.web --db demo_biblioteca.db
```

El generador de muestra se niega a modificar una base existente: si ya la creaste anteriormente, omití el primer comando. Cada base mantiene sus propios usuarios. Los nombres `biblioteca.db` y `demo_biblioteca.db` se buscan primero en la carpeta actual y, si no existen allí, en `backend/database/`; también podés pasar otra ruta explícita con `--db`. La interfaz está pensada para uso local; las sesiones se cierran al reiniciar el servidor.

## Configuración

Los valores ajustables están en `backend/configuracion.json`. Editá ese archivo y reiniciá el servidor o la consola para aplicarlos:

| Clave | Uso | Valor inicial |
|---|---|---|
| `base_datos` | Base usada cuando no se indica `--db` | `biblioteca.db` |
| `puerto` | Puerto web cuando no se indica `--port` | `8000` |
| `plazo_dias` | Días desde la entrega hasta el vencimiento | `14` |
| `multa_diaria_centavos` | Multa por día de atraso, en centavos | `10000` ($100) |
| `filas_por_pagina` | Cantidad de filas por página de las tablas | `10` |
| `idioma`, `moneda` | Formato de fechas, números e importes; los textos siguen en español | `es-AR`, `ARS` |
| `espera_busqueda_ms` | Espera antes de filtrar al escribir | `300` |
| `tiempo_solicitud_ms` | Límite de espera de las solicitudes tras la carga inicial | `15000` |
| `duracion_aviso_ms` | Tiempo visible de los avisos de éxito | `4800` |

Las reglas de estados se definen en `backend/models/modelo.py`, y los reportes en `backend/daos/reportes.py`. La web recibe esas definiciones del servidor. Los campos de alta y edición de sedes, socios y libros se comparten en `frontend/js/formularios.js`.

## Ejecución

Abrir una terminal en esta carpeta y ejecutar:

```powershell
.\.venv\Scripts\python.exe -m backend --help
.\.venv\Scripts\python.exe -m backend --db biblioteca.db sede-crear "Centro" "San Martín 100" "351-111" "L-V 9-18"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db sede-crear "Norte" "Colón 200" "351-222" "L-V 9-17"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db socio-crear 12345678 "Ana Pérez" "ana@example.com"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db libro-crear 9780000000001 "Diseño con objetos" "A. Autor" --anio 2026
.\.venv\Scripts\python.exe -m backend --db biblioteca.db ejemplar-crear EJ-001 1 1
.\.venv\Scripts\python.exe -m backend --db biblioteca.db disponibilidad
```

Cada comando devuelve JSON. Los IDs se asignan al crear registros y se consultan con `listar`:

```powershell
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar sedes
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar socios
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar libros
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar ejemplares
```

### Préstamo local

```powershell
.\.venv\Scripts\python.exe -m backend --db biblioteca.db prestamo-solicitar 1 1 1 1
.\.venv\Scripts\python.exe -m backend --db biblioteca.db prestamo-entregar 1
.\.venv\Scripts\python.exe -m backend --db biblioteca.db prestamo-devolver 1 --condicion BUENO
```

### Préstamo entre sedes

Los números `1 1 1 2` significan socio 1, ejemplar 1, sede de origen 1 y sede de destino 2. Usar un ejemplar disponible; si se ejecutó el ejemplo local, ya habrá sido devuelto.

```powershell
.\.venv\Scripts\python.exe -m backend --db biblioteca.db prestamo-solicitar 1 1 1 2
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar remitos
.\.venv\Scripts\python.exe -m backend --db biblioteca.db remito-avanzar 1 EMPAQUETADO --detalle "Caja sellada"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db remito-avanzar 1 DESPACHADO --detalle "Sale de Centro"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db remito-avanzar 1 RECIBIDO --detalle "Ingresa en Norte"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db remito-historial 1
.\.venv\Scripts\python.exe -m backend --db biblioteca.db prestamo-entregar 2
.\.venv\Scripts\python.exe -m backend --db biblioteca.db prestamo-devolver 2 --condicion BUENO
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar remitos
```

Al devolver un préstamo interbibliotecario, se crea un remito de regreso. Se lo avanza con `remito-avanzar` de la misma forma. Al recibirlo en la sede de origen, el ejemplar vuelve a estar disponible (o queda en revisión si se devolvió dañado).

### Reservas y administración

```powershell
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reserva-crear 1 1 1
.\.venv\Scripts\python.exe -m backend --db biblioteca.db listar reservas
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reserva-cancelar 1
.\.venv\Scripts\python.exe -m backend --db biblioteca.db socio-editar 1 --habilitado 0
.\.venv\Scripts\python.exe -m backend --db biblioteca.db sede-editar 2 --activa 0
.\.venv\Scripts\python.exe -m backend --db biblioteca.db libro-editar 1 --titulo "Nuevo título"
.\.venv\Scripts\python.exe -m backend --db biblioteca.db revision-cerrar 1 --apto 1
```

`revision-cerrar` solo corresponde a ejemplares en estado `EN_REVISION`. Las sedes y socios usan baja o inhabilitación lógica para conservar el historial. Se pueden editar dirección, contacto y horarios de sedes, y nombre y correo de socios.

### Reportes

```powershell
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reporte activos_transito
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reporte vencidos_multas
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reporte mas_solicitados
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reporte disponibilidad
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reporte logistica
.\.venv\Scripts\python.exe -m backend --db biblioteca.db reporte movimientos
```

Los seis reportes usan consultas agregadas o cruces de varias entidades. Sus definiciones y alcances figuran en [DISEÑO.md](DISEÑO.md).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Las pruebas usan bases SQLite temporales independientes. Cubren el circuito local e interbibliotecario, la trazabilidad, la persistencia, las reservas en orden, los duplicados, las sedes dadas de baja, los socios inhabilitados, las fechas, las multas, los reportes, las ediciones parciales, los comandos de consola y la API de la interfaz web.

## Organización

```text
backend/
  controllers/   Endpoints FastAPI, validación y autorización.
  services/      Casos de uso, operaciones y autenticación.
  database/      Conexión SQLite, esquema y bases de datos.
  daos/          Consultas y operaciones de persistencia.
  models/        Entidades, reglas y patrones del dominio.
  tests/         Pruebas automatizadas.
  configuracion.json
  requirements.txt
  __main__.py, web.py, demo.py
frontend/
  index.html, login.html
  css/           Estilos de la aplicación.
  js/            Interacciones, formularios y acceso.
```

En la raíz permanecen el enunciado y la documentación: `DISEÑO.md` describe el dominio y los patrones; `DESIGN.md` y `UX-CONTRACT.md` describen el diseño y la interacción.

La base `backend/database/biblioteca.db` se crea automáticamente al ejecutar el primer comando. Para comenzar una base nueva, utilizá otra ruta con `--db`.
