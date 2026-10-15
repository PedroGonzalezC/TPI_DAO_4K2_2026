"""Servidor web local para la interfaz del TPI, sin dependencias externas."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .servicio import Biblioteca, ReglaNegocio


STATIC = Path(__file__).resolve().parent.parent / "web"
MIME = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml"}
TABLAS = ("sedes", "socios", "libros", "ejemplares", "reservas", "prestamos", "remitos")
REPORTES = ("activos_transito", "vencidos_multas", "mas_solicitados", "disponibilidad", "logistica", "movimientos")


def _id(datos, nombre):
    try:
        valor = int(datos[nombre])
    except (KeyError, TypeError, ValueError) as exc:
        raise ReglaNegocio(f"{nombre} debe ser un número entero") from exc
    if valor <= 0:
        raise ReglaNegocio(f"{nombre} debe ser positivo")
    return valor


def _cadena(datos, nombre):
    valor = datos.get(nombre)
    if not isinstance(valor, str):
        raise ReglaNegocio(f"{nombre} es obligatorio")
    return valor


def ejecutar(b, datos):
    """Lista cerrada de operaciones; nunca ejecuta nombres enviados como método."""
    accion = datos.get("accion")
    if accion == "crear_sede":
        return b.crear_sede(*(_cadena(datos, x) for x in ("nombre", "direccion", "contacto", "horarios")))
    if accion == "editar_sede":
        return b.actualizar_sede(_id(datos, "id"), direccion=datos.get("direccion"),
                                 contacto=datos.get("contacto"), horarios=datos.get("horarios"),
                                 activa=datos.get("activa"))
    if accion == "crear_socio":
        return b.crear_socio(*(_cadena(datos, x) for x in ("documento", "nombre", "email")))
    if accion == "editar_socio":
        return b.actualizar_socio(_id(datos, "id"), nombre=datos.get("nombre"),
                                  email=datos.get("email"), habilitado=datos.get("habilitado"))
    if accion == "crear_libro":
        anio = datos.get("anio")
        return b.crear_libro(*(_cadena(datos, x) for x in ("isbn", "titulo", "autor")),
                             int(anio) if anio not in (None, "") else None)
    if accion == "editar_libro":
        anio = datos.get("anio")
        return b.actualizar_libro(_id(datos, "id"), titulo=datos.get("titulo"),
                                  autor=datos.get("autor"), anio=int(anio) if anio not in (None, "") else None)
    if accion == "crear_ejemplar":
        return b.crear_ejemplar(_cadena(datos, "codigo"), _id(datos, "libro_id"), _id(datos, "sede_id"))
    if accion == "reservar":
        return b.reservar(_id(datos, "socio_id"), _id(datos, "libro_id"), _id(datos, "sede_id"))
    if accion == "cancelar_reserva":
        return b.cancelar_reserva(_id(datos, "id"))
    if accion == "solicitar_prestamo":
        return b.solicitar_prestamo(*(_id(datos, x) for x in
            ("socio_id", "ejemplar_id", "sede_origen_id", "sede_destino_id")))
    if accion == "entregar_prestamo":
        return {"vence_en": b.entregar_prestamo(_id(datos, "id"))}
    if accion == "devolver_prestamo":
        return {"multa_centavos": b.devolver_prestamo(_id(datos, "id"), _cadena(datos, "condicion"))}
    if accion == "avanzar_remito":
        return b.avanzar_remito(_id(datos, "id"), _cadena(datos, "estado"), detalle=datos.get("detalle", ""))
    if accion == "cerrar_revision":
        apto = datos.get("apto")
        if not isinstance(apto, bool):
            raise ReglaNegocio("apto debe ser verdadero o falso")
        return b.cerrar_revision(_id(datos, "ejemplar_id"), apto)
    raise ReglaNegocio("Operación desconocida")


def crear_servidor(ruta_db, puerto=8000):
    biblioteca = Biblioteca(ruta_db)
    nombre_base = Path(ruta_db).name

    class Handler(BaseHTTPRequestHandler):
        def _origen_local(self):
            puerto_actual = self.server.server_port
            permitidos = {f"127.0.0.1:{puerto_actual}", f"localhost:{puerto_actual}"}
            if self.headers.get("Host") not in permitidos:
                self._json(403, {"error": "Acceso local no permitido"})
                return False
            origen = self.headers.get("Origin")
            if origen and origen not in {f"http://{host}" for host in permitidos}:
                self._json(403, {"error": "Origen no permitido"})
                return False
            return True

        def _json(self, codigo, datos):
            cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_GET(self):
            if not self._origen_local():
                return
            ruta = urlparse(self.path).path
            try:
                if ruta == "/api/state":
                    self._json(200, {"tablas": {t: biblioteca.listar(t) for t in TABLAS},
                                     "reportes": {r: biblioteca.reportes(r) for r in REPORTES},
                                     "base": {"nombre": nombre_base, "demo": nombre_base.startswith("demo_")}})
                    return
                if ruta.startswith("/api/remito/") and ruta.endswith("/historial"):
                    remito_id = int(ruta.split("/")[3])
                    self._json(200, biblioteca.historial_remito(remito_id))
                    return
                archivo = {"/": "index.html", "/index.html": "index.html",
                           "/styles.css": "styles.css", "/app.js": "app.js"}.get(ruta)
                if not archivo:
                    self._json(404, {"error": "Página no encontrada"})
                    return
                path = STATIC / archivo
                contenido = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", f"{MIME[path.suffix]}; charset=utf-8")
                self.send_header("Content-Length", str(len(contenido)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(contenido)
            except (ReglaNegocio, ValueError) as exc:
                self._json(400, {"error": str(exc)})
            except OSError:
                self._json(500, {"error": "No se pudo leer el recurso. Reintentá la operación."})

        def do_POST(self):
            if not self._origen_local():
                return
            if urlparse(self.path).path != "/api/action":
                self._json(404, {"error": "Operación no encontrada"})
                return
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                self._json(415, {"error": "Se requiere JSON"})
                return
            try:
                largo = int(self.headers.get("Content-Length", "0"))
                if largo <= 0 or largo > 1_000_000:
                    self._json(413, {"error": "Solicitud demasiado grande"})
                    return
                datos = json.loads(self.rfile.read(largo))
                if not isinstance(datos, dict):
                    raise ReglaNegocio("El cuerpo debe ser un objeto")
                self._json(200, {"resultado": ejecutar(biblioteca, datos)})
            except (ReglaNegocio, ValueError, TypeError) as exc:
                self._json(400, {"error": str(exc)})
            except Exception:
                self._json(500, {"error": "No se pudo completar la operación. Comprobá los datos y reintentá."})

    return ThreadingHTTPServer(("127.0.0.1", puerto), Handler)


def main():
    parser = argparse.ArgumentParser(description="Interfaz web local de la biblioteca")
    parser.add_argument("--db", default="biblioteca.db", help="Ruta de la base SQLite")
    parser.add_argument("--port", type=int, default=8000, help="Puerto local (por defecto 8000)")
    args = parser.parse_args()
    servidor = crear_servidor(args.db, args.port)
    print(f"Biblioteca disponible en http://127.0.0.1:{servidor.server_port}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
