import json
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from biblioteca.web import crear_servidor


class TestWeb(TestCase):
    def setUp(self):
        carpeta = Path(__file__).parent / ".tmp"
        carpeta.mkdir(exist_ok=True)
        self.temporal = TemporaryDirectory(dir=carpeta)
        self.servidor = crear_servidor(Path(self.temporal.name) / "web.db", 0)
        self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.servidor.server_port}"

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.thread.join(timeout=3)
        self.temporal.cleanup()

    def get(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return response.status, json.load(response)

    def post(self, data):
        request = Request(self.base + "/api/action", json.dumps(data).encode(),
                          {"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=3) as response:
            return response.status, json.load(response)

    def test_api_creacion_y_estado(self):
        status, data = self.get("/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(data["tablas"]["sedes"], [])
        status, result = self.post({"accion": "crear_sede", "nombre": "Centro",
                                    "direccion": "Calle 1", "contacto": "111", "horarios": "9-18"})
        self.assertEqual(status, 200)
        self.assertEqual(result["resultado"], 1)
        self.assertEqual(self.get("/api/state")[1]["tablas"]["sedes"][0]["nombre"], "Centro")

    def test_api_rechaza_regla_y_recurso_inexistente(self):
        self.post({"accion": "crear_sede", "nombre": "Centro", "direccion": "Calle 1",
                   "contacto": "111", "horarios": "9-18"})
        with self.assertRaises(HTTPError) as ctx:
            self.post({"accion": "crear_sede", "nombre": "Centro", "direccion": "Otra",
                       "contacto": "222", "horarios": "9-18"})
        self.assertEqual(ctx.exception.code, 400)
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + "/api/inexistente", timeout=3)
        self.assertEqual(ctx.exception.code, 404)

    def test_interfaz_se_sirve_como_html(self):
        with urlopen(self.base + "/", timeout=3) as response:
            html = response.read().decode("utf-8")
            self.assertIn("Red de Bibliotecas", html)
            self.assertIn("text/html", response.headers["Content-Type"])
