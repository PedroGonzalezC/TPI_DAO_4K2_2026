"""Manejador de la API y los archivos estáticos locales."""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from ..dominio.regla_negocio import ReglaNegocio
from ..config import RAIZ_PROYECTO
from .web_actions import ejecutar

STATIC = RAIZ_PROYECTO / "web"
MIME = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml"}
TABLAS = ("sedes", "socios", "libros", "ejemplares", "reservas", "prestamos", "remitos")
REPORTES = ("activos_transito", "vencidos_multas", "mas_solicitados", "disponibilidad", "logistica", "movimientos")


class ManejadorWeb(BaseHTTPRequestHandler):
    def __init__(self, *args, biblioteca, nombre_base, **kwargs):
        self.biblioteca = biblioteca
        self.nombre_base = nombre_base
        super().__init__(*args, **kwargs)

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
                self._json(200, {"tablas": {t: self.biblioteca.listar(t) for t in TABLAS},
                                 "reportes": {r: self.biblioteca.reportes(r) for r in REPORTES},
                                 "base": {"nombre": self.nombre_base, "demo": self.nombre_base.startswith("demo_")}})
                return
            if ruta.startswith("/api/remito/") and ruta.endswith("/historial"):
                remito_id = int(ruta.split("/")[3])
                self._json(200, self.biblioteca.historial_remito(remito_id))
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
            self._json(200, {"resultado": ejecutar(self.biblioteca, datos)})
        except (ReglaNegocio, ValueError, TypeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception:
            self._json(500, {"error": "No se pudo completar la operación. Comprobá los datos y reintentá."})

