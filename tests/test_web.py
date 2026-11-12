from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from fastapi.testclient import TestClient

from backend.web import crear_app


class TestWebControllers(TestCase):
    def setUp(self):
        carpeta = Path(__file__).parent / ".tmp"
        carpeta.mkdir(exist_ok=True)
        self.temporal = TemporaryDirectory(dir=carpeta)
        self.app = crear_app(Path(self.temporal.name) / "web.db")
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.temporal.cleanup()

    def test_api_rest_creacion_y_listado(self):
        res_sedes = self.client.get("/api/sedes")
        self.assertEqual(res_sedes.status_code, 200)
        self.assertEqual(res_sedes.json(), [])

        res_crear = self.client.post(
            "/api/sedes",
            json={
                "nombre": "Centro",
                "direccion": "Calle 1",
                "contacto": "111",
                "horarios": "9-18",
            },
        )
        self.assertEqual(res_crear.status_code, 201)
        self.assertEqual(res_crear.json()["id"], 1)

        sedes = self.client.get("/api/sedes").json()
        self.assertEqual(len(sedes), 1)
        self.assertEqual(sedes[0]["nombre"], "Centro")

    def test_api_circuito_completo_prestamo_y_remito(self):
        sede_origen = self.client.post(
            "/api/sedes",
            json={"nombre": "Centro", "direccion": "C1", "contacto": "1", "horarios": "9-18"},
        ).json()["id"]
        sede_destino = self.client.post(
            "/api/sedes",
            json={"nombre": "Norte", "direccion": "C2", "contacto": "2", "horarios": "9-18"},
        ).json()["id"]
        socio = self.client.post(
            "/api/socios",
            json={"documento": "30111222", "nombre": "Ana", "email": "ana@example.com"},
        ).json()["id"]
        libro = self.client.post(
            "/api/materiales",
            json={"isbn": "978-950-001", "titulo": "Arquitectura en Capas", "autor": "Autor", "anio": 2026},
        ).json()["id"]
        ejemplar = self.client.post(
            "/api/ejemplares",
            json={"codigo": "EJ-100", "libro_id": libro, "sede_id": sede_origen},
        ).json()["id"]

        res_prestamo = self.client.post(
            "/api/solicitudes",
            json={
                "socio_id": socio,
                "ejemplar_id": ejemplar,
                "sede_origen_id": sede_origen,
                "sede_destino_id": sede_destino,
                "plazo_dias": 10,
            },
        )
        self.assertEqual(res_prestamo.status_code, 201)
        prestamo_id = res_prestamo.json()["id"]
        self.assertEqual(self.client.get("/api/prestamos").json()[0]["plazo_dias"], 10)
        self.assertEqual(self.client.get("/api/ejemplares").json()[0]["condicion"], "BUENO")

        remitos = self.client.get("/api/remitos").json()
        self.assertEqual(len(remitos), 1)
        remito_id = remitos[0]["id"]

        for estado in ("EMPAQUETADO", "DESPACHADO", "RECIBIDO"):
            r = self.client.post(
                f"/api/remitos/{remito_id}/avanzar",
                json={"estado": estado, "detalle": f"Paso a {estado}"},
            )
            self.assertEqual(r.status_code, 200)

        historial = self.client.get(f"/api/remitos/{remito_id}/historial").json()
        self.assertEqual([h["estado"] for h in historial], ["CREADO", "EMPAQUETADO", "DESPACHADO", "RECIBIDO"])

        entrega = self.client.post(f"/api/prestamos/{prestamo_id}/entregar")
        self.assertEqual(entrega.status_code, 200)
        self.assertIn("vence_en", entrega.json())

        devolucion = self.client.post(
            f"/api/prestamos/{prestamo_id}/devolver",
            json={"condicion": "BUENO"},
        )
        self.assertEqual(devolucion.status_code, 200)
        self.assertEqual(devolucion.json()["multa_centavos"], 0)

    def test_api_traduce_errores_de_negocio_validacion_y_autorizacion(self):
        self.client.post(
            "/api/sedes",
            json={"nombre": "Centro", "direccion": "Calle 1", "contacto": "111", "horarios": "9-18"},
        )
        duplicada = self.client.post(
            "/api/sedes",
            json={"nombre": "Centro", "direccion": "Otra", "contacto": "222", "horarios": "9-18"},
        )
        self.assertEqual(duplicada.status_code, 400)
        self.assertIn("error", duplicada.json())

        invalido = self.client.post("/api/sedes", json={"nombre": ""})
        self.assertEqual(invalido.status_code, 400)

        no_encontrado = self.client.patch("/api/sedes/999", json={"direccion": "Nueva"})
        self.assertEqual(no_encontrado.status_code, 404)

        no_autorizado = self.client.post(
            "/api/sedes",
            json={"nombre": "Sur", "direccion": "Calle 3", "contacto": "333", "horarios": "9-18"},
            headers={"X-Usuario": "socio-1", "X-Rol": "SOCIO"},
        )
        self.assertEqual(no_autorizado.status_code, 403)

        ruta_inexistente = self.client.get("/api/inexistente")
        self.assertEqual(ruta_inexistente.status_code, 404)

    def test_interfaz_se_sirve_como_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Red de Bibliotecas", response.text)
        self.assertIn("text/html", response.headers["content-type"])
        bundle = self.client.get("/src/App.jsx")
        self.assertEqual(bundle.status_code, 200)
        self.assertIn("ReactDOM.createRoot", bundle.text)
        self.assertIn("VistaPrestamos", bundle.text)

    def test_endpoints_delete(self):
        sede = self.client.post(
            "/api/sedes",
            json={"nombre": "Norte", "direccion": "Av 1", "contacto": "111", "horarios": "9-18"},
        ).json()["id"]
        socio = self.client.post(
            "/api/socios",
            json={"documento": "40111222", "nombre": "Juan", "email": "juan@test.com"},
        ).json()["id"]
        libro = self.client.post(
            "/api/libros",
            json={"isbn": "9780001112223", "titulo": "Temporal", "autor": "Autor", "anio": 2024},
        ).json()["id"]
        ejemplar = self.client.post(
            "/api/ejemplares",
            json={"codigo": "N-01", "libro_id": libro, "sede_id": sede},
        ).json()["id"]
        prestamo = self.client.post(
            "/api/prestamos",
            json={"socio_id": socio, "ejemplar_id": ejemplar, "sede_origen_id": sede, "sede_destino_id": sede},
        ).json()["id"]

        res_cancel = self.client.delete(f"/api/prestamos/{prestamo}")
        self.assertEqual(res_cancel.status_code, 200)
        self.assertEqual(self.client.get("/api/prestamos").json()[0]["estado"], "CANCELADO")

        res_ejemplar = self.client.delete(f"/api/ejemplares/{ejemplar}")
        self.assertEqual(res_ejemplar.status_code, 200)
        self.assertEqual(res_ejemplar.json()["resultado"], "baja_logica")

        libro_vacio = self.client.post(
            "/api/libros",
            json={"isbn": "9780009998887", "titulo": "Borrable", "autor": "Autor", "anio": 2024},
        ).json()["id"]
        res_libro = self.client.delete(f"/api/libros/{libro_vacio}")
        self.assertEqual(res_libro.status_code, 200)
        self.assertEqual(res_libro.json()["resultado"], "eliminado")

